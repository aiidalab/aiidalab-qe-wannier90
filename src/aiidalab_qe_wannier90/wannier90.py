"""AiiDAlab QE plugin for Wannier90 calculations."""

from aiidalab_qe.plugins import QeAppPlugin


class Wannier90Plugin(QeAppPlugin):
    @property
    def outline(self) -> str:
        return 'Wannier functions'

    def configuration(self):
        from .model import Wannier90ConfigurationSettingsModel
        from .setting import Wannier90ConfigurationSettingPanel

        return {
            'panel': Wannier90ConfigurationSettingPanel,
            'model': Wannier90ConfigurationSettingsModel,
        }

    def resources(self):
        from .resources import (
            Wannier90ResourceSettingsModel,
            Wannier90ResourceSettingsPanel,
        )

        return {
            'panel': Wannier90ResourceSettingsPanel,
            'model': Wannier90ResourceSettingsModel,
        }

    def workchain(self):
        from .workchain import workchain_and_builder

        return workchain_and_builder

    def result(self):
        from .result import Wannier90ResultsModel, Wannier90ResultsPanel

        return {
            'panel': Wannier90ResultsPanel,
            'model': Wannier90ResultsModel,
        }

    def guides(self):
        from pathlib import Path

        return {
            'title': 'Wannier functions',
            'path': Path(__file__).resolve().parent / 'guides',
        }
