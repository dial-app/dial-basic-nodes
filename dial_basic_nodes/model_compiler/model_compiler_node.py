# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

from typing import TYPE_CHECKING

import dependency_injector.providers as providers
from tensorflow.keras import Model

from dial_core.datasets import Dataset
from dial_core.node_editor import InputPort, Node, OutputPort
from dial_core.utils import Dial

from .model_compiler_widget import ModelCompilerWidgetFactory

if TYPE_CHECKING:
    from .model_compiler_widget import ModelCompilerWidget


class ModelCompilerNode(Node):
    def __init__(self, model_compiler_widget: "ModelCompilerWidget"):
        super().__init__(
            title="Model Compiler Node", inner_widget=model_compiler_widget,
        )

        # Ports
        self.add_input_port(InputPort("dataset", port_type=Dataset))
        self.add_input_port(InputPort("layers", port_type=dial_core.KerasLayerListMIME))

        self.add_output_port(OutputPort("model", port_type=Model))
        self.outputs["model"].output_generator = self.get_model

    def get_model(self):
        raise NotImplementedError("get_model is not implemented!")


ModelCompilerNodeFactory = providers.Factory(
    ModelCompilerNode, model_compiler_widget=ModelCompilerWidgetFactory
)
