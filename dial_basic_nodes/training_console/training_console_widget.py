# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

from enum import Enum
from typing import Dict, Optional

import dependency_injector.providers as providers
from dial_core.datasets import Dataset
from dial_core.utils import log
from PySide2.QtCore import QObject, QSize, Qt, QThread, Signal
from PySide2.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from tensorflow import keras
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model

LOGGER = log.get_logger(__name__)


class SignalsCallback(keras.callbacks.Callback, QObject):
    epoch_begin = Signal(int, dict)
    epoch_end = Signal(int, dict)
    train_batch_end = Signal(int, dict)
    train_end = Signal(dict)

    def __init__(self, batches_between_updates: int = 100):
        keras.callbacks.Callback.__init__(self)
        QObject.__init__(self)

        self.batches_between_updates = batches_between_updates

    def on_train_batch_end(self, batch: int, logs=None):
        if batch % self.batches_between_updates == 0:
            self.train_batch_end.emit(batch, logs)

    def on_train_end(self, logs=None):
        self.train_end.emit(logs)

    def on_epoch_begin(self, epoch: int, logs=None):
        self.epoch_begin.emit(epoch, logs)

    def on_epoch_end(self, epoch: int, logs=None):
        self.epoch_end.emit(epoch, logs)

    def stop_model(self):
        self.model.stop_training = True


class FitWorker(QThread):
    def __init__(self, model, train_dataset, hyperparameters, callbacks):
        super().__init__()

        self.__model = model
        self.__train_dataset = train_dataset
        self.__hyperparameters = hyperparameters
        self.__callbacks = callbacks

    def run(self):
        self.__model.fit(
            self.__train_dataset,
            epochs=self.__hyperparameters["epochs"],
            callbacks=self.__callbacks,
        )


class TrainingConsoleWidget(QWidget):
    """The TrainingConsoleWidget provides a widget for controlling the training status
    of a model, in a simple way. (Analog of the console output in Keras, but with a few
    more options).

    It also can save and show an history of the last trained models.
    """

    training_started = Signal()
    training_stopped = Signal()

    class TrainingStatus(Enum):
        Running = 1
        Stopped = 2
        Not_Compiled = 3

    def __init__(self, parent: "QWidget" = None):
        super().__init__(parent)

        # Components
        self.__pretrained_model: Optional["keras.models.Model"] = None
        self.__train_dataset: Optional["Dataset"] = None
        self.__validation_dataset: Optional["Dataset"] = None
        self.__hyperparameters: Optional[Dict] = None

        self.__trained_model: Optional["keras.models.Model"] = None

        # Widgets
        self.__start_training_button = QPushButton("Start training")
        self.__stop_training_button = QPushButton("Stop training")

        self.__buttons_layout = QHBoxLayout()
        self.__buttons_layout.addWidget(self.__start_training_button)
        self.__buttons_layout.addWidget(self.__stop_training_button)

        self.__status_label = QLabel()

        self.__batch_progress_bar = QProgressBar()
        self.__epoch_progress_bar = QProgressBar()

        self.training_output_textbox = QPlainTextEdit()
        self.training_output_textbox.setReadOnly(True)

        console_output_group = QGroupBox("Console output")
        console_output_layout = QVBoxLayout()
        console_output_layout.setContentsMargins(0, 0, 0, 0)
        console_output_layout.addWidget(self.training_output_textbox)
        console_output_group.setLayout(console_output_layout)

        self.__main_layout = QVBoxLayout()
        self.__main_layout.addLayout(self.__buttons_layout)
        self.__main_layout.addWidget(self.__status_label, Qt.AlignRight)
        self.__main_layout.addWidget(console_output_group)
        self.__main_layout.addWidget(self.__batch_progress_bar)
        self.__main_layout.addWidget(self.__epoch_progress_bar)
        self.setLayout(self.__main_layout)

        # Connections
        self.__start_training_button.clicked.connect(self.start_training)
        self.__stop_training_button.clicked.connect(self.stop_training)

        # Inner workings
        self.training_status = self.TrainingStatus.Not_Compiled
        self.__training_thread = None

    @property
    def training_status(self):
        """Returns the current status of the training (Running, Stopped...)"""
        return self.__training_status

    @training_status.setter
    def training_status(self, new_status):
        """Changes the training status.

        Doing so will update the interface accordingly.
        """
        self.__training_status = new_status

        if self.__training_status == self.TrainingStatus.Running:
            self.__start_training_button.setEnabled(False)
            self.__stop_training_button.setEnabled(True)
            self.__status_label.setText("Running")
            self.start_training

        elif self.__training_status == self.TrainingStatus.Stopped:
            self.__start_training_button.setEnabled(True)
            self.__stop_training_button.setEnabled(False)
            self.__status_label.setText("Stopped")

        elif self.__train_dataset == self.TrainingStatus.Not_Compiled:
            self.__start_training_button.setEnabled(True)
            self.__stop_training_button.setEnabled(False)
            self.__status_label.setText("Not Compiled")

    def set_train_dataset(self, train_dataset: "Dataset"):
        """Sets a new training dataset."""
        self.__train_dataset = train_dataset

        self.training_status = self.TrainingStatus.Not_Compiled

    def set_validation_dataset(self, validation_dataset: "Dataset"):
        """Sets a new validation dataset."""
        self.__validation_dataset = validation_dataset

    def set_pretrained_model(self, pretrained_model: "Model"):
        """Sets a new pretrained model for training."""
        self.__pretrained_model = pretrained_model

        self.training_status = self.TrainingStatus.Not_Compiled

    def set_hyperparameters(self, hyperparameters: Dict):
        """Sets new hyperparameters for training."""
        self.__hyperparameters = hyperparameters

        self.training_status = self.TrainingStatus.Not_Compiled

    def get_trained_model(self):
        """Returns the model after it has been trained."""
        return self.__trained_model

    def compile_model(self):
        """Compile the model with the passed hyperparameters. The dataset is needed for
        the input shape."""
        LOGGER.info("Starting to compile the model...")

        if not self.__is_input_ready():
            return False

        # Create a new model based on the pretrained one, but with a new InputLayer
        # compatible with the dataset
        input_layer = Input(self.__train_dataset.input_shape)
        output = self.__pretrained_model(input_layer)

        self.__trained_model = Model(input_layer, output)

        try:
            self.__trained_model.compile(
                optimizer=self.__hyperparameters["optimizer"],
                loss=self.__hyperparameters["loss_function"],
                metrics=["accuracy"],
            )

            self.__trained_model.summary()

            LOGGER.info("Model compiled successfully!!")

            self.training_status = self.TrainingStatus.Stopped

            return True

        except Exception as err:
            LOGGER.exception("Model Compiling error: ", err)

            self.training_output_textbox.setPlainText(
                "> Error while compiling the model:\n", str(err)
            )

        return False

    def start_training(self):
        """Starts the training on a new thread."""
        if self.training_status == self.TrainingStatus.Not_Compiled:
            successfully_compiled = self.compile_model()

            if not successfully_compiled:
                LOGGER.info("Couldn't compile model. Training not started.")
                return

        total_train_batches = len(self.__train_dataset)
        total_train_epochs = self.__hyperparameters["epochs"]

        self.__batch_progress_bar.setMaximum(total_train_batches)
        self.__epoch_progress_bar.setMaximum(total_train_epochs)
        self.__epoch_progress_bar.setValue(0)
        self.training_output_textbox.clear()

        def epoch_begin_update(epoch: int, logs):
            message = f"==== Epoch {epoch + 1}/{total_train_epochs} ===="

            LOGGER.info(message)
            self.training_output_textbox.appendPlainText(message)
            self.__epoch_progress_bar.setValue(epoch)

        def batch_end_update(batch: int, logs):
            # Update progress
            self.__batch_progress_bar.setValue(batch)

            # Log metrics on console
            message = f'{logs["batch"]}/{total_train_batches}'

            for (k, v) in list(logs.items())[2:]:
                message += f" - {k}: {v:.4f}"

            LOGGER.info(message)
            self.training_output_textbox.appendPlainText(message)

        def train_end_update(logs):
            # Put the progress bar at 100% when the training ends
            self.__batch_progress_bar.setValue(self.__batch_progress_bar.maximum())
            self.__epoch_progress_bar.setValue(self.__epoch_progress_bar.maximum())

            # Stop the training
            self.stop_training()

        # Connect callbacks
        signals_callback = SignalsCallback()
        signals_callback.epoch_begin.connect(epoch_begin_update)
        signals_callback.train_batch_end.connect(batch_end_update)
        signals_callback.train_end.connect(train_end_update)

        self.training_stopped.connect(signals_callback.stop_model)

        # Start training
        self.__fit_worker = FitWorker(
            self.__trained_model,
            self.__train_dataset,
            self.__hyperparameters,
            [signals_callback],
        )

        self.training_status = self.TrainingStatus.Running
        self.__fit_worker.start()

        self.training_started.emit()

    def stop_training(self):
        """Stops the training."""
        self.training_status = self.TrainingStatus.Stopped

        self.training_stopped.emit()

    def __is_input_ready(self) -> bool:
        """Checks if the input values used for training (model, dataset,
        hyperparameters...) are valid."""
        message = ""

        if not self.__train_dataset:
            message += "> Training dataset not specified\n"

        if not self.__pretrained_model:
            message += "> Model not specified.\n"

        if not self.__hyperparameters:
            message += "> Hyperparameters not specified.\n"

        if message:
            self.training_output_textbox.setPlainText(message)
            LOGGER.info(message)
            return False

        return True

    def sizeHint(self) -> "QSize":
        """Returns the expected size of the widget."""
        return QSize(500, 300)

    def __reduce__(self):
        return (TrainingConsoleWidget, ())


TrainingConsoleWidgetFactory = providers.Factory(TrainingConsoleWidget)