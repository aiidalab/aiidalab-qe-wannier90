from aiidalab_qe.common.panel import ResultsModel
from aiida.common.extendeddicts import AttributeDict


class Wannier90ResultsModel(ResultsModel):
    title = 'Wannier90'
    identifier = 'wannier90'

    _this_process_label = 'QeAppWannier90BandsWorkChain'

    def get_bands_node(self):
        outputs = self._get_child_outputs()
        pw_bands = outputs.pw_bands
        wannier90_bands = AttributeDict()
        for key in pw_bands.keys():
            wannier90_bands[key] = pw_bands[key]
        wannier90_bands['band_structure'] = outputs.wannier90_bands.band_structure
        return pw_bands, wannier90_bands
