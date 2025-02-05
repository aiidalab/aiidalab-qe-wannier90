"""Wannier90 results view widgets"""

from aiidalab_qe.common.bands_pdos import BandsPdosModel, BandsPdosWidget
from aiidalab_qe.common.panel import ResultsPanel

from .model import Wannier90ResultsModel


class Wannier90ResultsPanel(ResultsPanel[Wannier90ResultsModel]):
    def _render(self):
        pw_bands, wannier90_bands = self._model.get_bands_node()
        model = BandsPdosModel(bands=pw_bands, wannier90_bands=wannier90_bands)
        widget = BandsPdosWidget(model=model)
        widget.render()
        self.children = [widget]
