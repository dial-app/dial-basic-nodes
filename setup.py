# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')

setup(
    long_description=readme,
    name='dial-basic-nodes',
    version='0.4a0',
    description='Basic nodes for the Dial app.',
    python_requires='<3.8,>=3.6',
    project_urls={
        "homepage": "https://github.com/dial-app/dial-basic-nodes",
        "repository": "https://github.com/dial-app/dial-basic-nodes"
    },
    author='David Afonso',
    author_email='davafons@gmail.com',
    license='GPL-3.0-only',
    keywords='deep-learning dial-app',
    packages=[
        'dial_basic_nodes', 'dial_basic_nodes.dataset_editor',
        'dial_basic_nodes.dataset_editor.dataset_table',
        'dial_basic_nodes.dataset_editor.datasets_list',
        'dial_basic_nodes.hyperparameters_config',
        'dial_basic_nodes.layers_editor',
        'dial_basic_nodes.layers_editor.layers_tree',
        'dial_basic_nodes.layers_editor.layers_tree.abstract_tree_model',
        'dial_basic_nodes.layers_editor.model_table',
        'dial_basic_nodes.test_model',
        'dial_basic_nodes.test_model.test_dataset_table',
        'dial_basic_nodes.training_console', 'dial_basic_nodes.utils',
        'dial_basic_nodes.utils.dataset_table'
    ],
    package_dir={"": "."},
    package_data={},
    install_requires=['dial-core', 'dial-gui'],
    dependency_links=['/home/david/dial-core', '/home/david/dial-gui'],
    extras_require={
        "dev": [
            "black==19.*,>=19.10.0", "docstr-coverage==1.*,>=1.0.5",
            "flake8==3.*,>=3.7.9", "isort==4.*,>=4.3.21", "mypy==0.*,>=0.770.0",
            "pre-commit==2.*,>=2.1.1", "pylint==2.*,>=2.4.4",
            "pytest==5.*,>=5.4.1", "pytest-cov==2.*,>=2.8.1",
            "pytest-qt==3.*,>=3.3.0", "sphinx==2.*,>=2.4.4",
            "sphinx-autodoc-typehints==1.*,>=1.10.3",
            "sphinx-rtd-theme==0.*,>=0.4.3", "taskipy==1.*,>=1.2.0",
            "tox==3.*,>=3.14.5"
        ]
    },
)
