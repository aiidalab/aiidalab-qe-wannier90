import traitlets as tl

from aiida import orm
from aiida_quantumespresso.calculations.functions.create_kpoints_from_distance import (
    create_kpoints_from_distance,
)
from aiida_quantumespresso.workflows.pdos import PdosWorkChain
from aiidalab_qe.common.mixins import HasInputStructure
from aiidalab_qe.common.panel import ConfigurationSettingsModel


class ConfigurationSettingsModel(ConfigurationSettingsModel, HasInputStructure):
    title = 'Wannier90'
    identifier = 'wannier90'

    dependencies = [
        'input_structure',
        'workchain.protocol',
    ]

    protocol = tl.Unicode(allow_none=True)

    def get_model_state(self):
        return {}

    def set_model_state(self, parameters: dict):
        pass
