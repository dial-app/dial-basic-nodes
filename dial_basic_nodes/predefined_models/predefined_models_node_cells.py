# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

import nbformat as nbf
from dial_core.notebook import NodeCells


class PredefinedModelsNodeCells(NodeCells):
    def _body_cells(self):
        return [nbf.v4.new_code_cell("# TODO: Implement later")]
