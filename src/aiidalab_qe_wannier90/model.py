import traitlets as tl
from aiida import orm
from aiida_quantumespresso.calculations.functions.create_kpoints_from_distance import (
    create_kpoints_from_distance,
)
from aiida_wannier90_workflows.workflows.base.wannier90 import (
    Wannier90BaseWorkChain,
)
from aiidalab_qe.common.mixins import HasInputStructure
from aiidalab_qe.common.panel import ConfigurationSettingsModel


class ConfigurationSettingsModel(ConfigurationSettingsModel, HasInputStructure):
    title = 'Wannier functions'
    identifier = 'wannier90'

    dependencies = [
        'input_structure',
        'workchain.protocol',
        'workchain.electronic_type',
    ]
    # by default: exclude semicore orbitals in both methods, since these low-energy states correspond
    # to almost flat bands and do not play any role in the chemistry of the materials
    exclude_semicore = tl.Bool(allow_none=True, default_value=True)
    scan_pdwf_parameter = tl.Bool(allow_none=True, default_value=False)
    plot_wannier_functions = tl.Bool(allow_none=True, default_value=False)
    number_of_disproj_max = tl.Int(allow_none=True, default_value=15)
    number_of_disproj_min = tl.Int(allow_none=True, default_value=2)
    retrieve_hamiltonian = tl.Bool(allow_none=True, default_value=True)
    retrieve_matrices = tl.Bool(allow_none=True, default_value=False)
    nscf_kpoints_distance = tl.Float(0.1)
    mesh_grid = tl.Unicode('')
    projection_type = tl.Unicode(allow_none=True, default_value='atomic_projectors_qe')
    frozen_type = tl.Unicode(allow_none=True, default_value='fixed_plus_projectability')
    energy_window_input = tl.Float(allow_none=True, default_value=2.0)
    compute_fermi_surface = tl.Bool(allow_none=True, default_value=False)
    fermi_surface_kpoint_distance = tl.Float(allow_none=True, default_value=0.04)
    compute_dhva_frequencies = tl.Bool(allow_none=True, default_value=False)
    # dHvA frequencies
    dhva_starting_phi = tl.Float(allow_none=True, default_value=0.0)
    dhva_starting_theta = tl.Float(allow_none=True, default_value=90.0)
    dhva_ending_phi = tl.Float(allow_none=True, default_value=90.0)
    dhva_ending_theta = tl.Float(allow_none=True, default_value=90.0)
    dhva_num_rotation = tl.Int(allow_none=True, default_value=90)

    protocol = tl.Unicode(allow_none=True)
    electronic_type = tl.Unicode(allow_none=True)

    def update(self, specific=''):
        with self.hold_trait_notifications():
            if not specific or specific != 'mesh':
                self._update_nscf_kpoints_distance()
            self._update_kpoints_mesh()

    def _check_blockers(self):
        if self.electronic_type == 'insulator':
            return [
                (
                    'Wannier90 automated workflows currently require the system to be treated '
                    'as a metal (include some conduction bands). Please set the electronic type '
                    'to Metal to proceed.'
                )
            ]
        return []

    def get_model_state(self):
        state = {
            'exclude_semicore': self.exclude_semicore,
            'plot_wannier_functions': self.plot_wannier_functions,
            'retrieve_hamiltonian': self.retrieve_hamiltonian,
            'retrieve_matrices': self.retrieve_matrices,
            'number_of_disproj_max': self.number_of_disproj_max,
            'number_of_disproj_min': self.number_of_disproj_min,
            'projection_type': self.projection_type,
            'frozen_type': self.frozen_type,
            'energy_window_input': self.energy_window_input,
            'compute_fermi_surface': self.compute_fermi_surface,
            'scan_pdwf_parameter': self.scan_pdwf_parameter,
            'nscf_kpoints_distance': self.nscf_kpoints_distance,
        }
        if self.compute_fermi_surface:
            state |= {
                'fermi_surface_kpoint_distance': self.fermi_surface_kpoint_distance,
                'compute_dhva_frequencies': self.compute_dhva_frequencies,
            }
            if self.compute_dhva_frequencies:
                state |= {
                    'dHvA_frequencies_parameters': {
                        'starting_phi': self.dhva_starting_phi,
                        'starting_theta': self.dhva_starting_theta,
                        'ending_phi': self.dhva_ending_phi,
                        'ending_theta': self.dhva_ending_theta,
                        'num_rotation': self.dhva_num_rotation,
                    },
                }
        return state

    def set_model_state(self, parameters: dict):
        self.exclude_semicore = parameters.get('exclude_semicore', True)
        self.plot_wannier_functions = parameters.get('plot_wannier_functions', False)
        self.number_of_disproj_max = parameters.get('number_of_disproj_max', 15)
        self.number_of_disproj_min = parameters.get('number_of_disproj_min', 2)
        self.compute_dhva_frequencies = parameters.get('compute_dhva_frequencies', False)
        self.dhva_ending_phi = parameters.get('dHvA_frequencies_parameters', {}).get('ending_phi', 90.0)
        self.dhva_ending_theta = parameters.get('dHvA_frequencies_parameters', {}).get('ending_theta', 90.0)
        self.dhva_starting_phi = parameters.get('dHvA_frequencies_parameters', {}).get('starting_phi', 0.0)
        self.dhva_starting_theta = parameters.get('dHvA_frequencies_parameters', {}).get('starting_theta', 90.0)
        self.dhva_num_rotation = parameters.get('dHvA_frequencies_parameters', {}).get('num_rotation', 90)
        self.scan_pdwf_parameter = parameters.get('scan_pdwf_parameter', False)
        self.nscf_kpoints_distance = parameters.get(
            'nscf_kpoints_distance',
            self._get_default('nscf_kpoints_distance'),
        )

    def reset(self):
        with self.hold_trait_notifications():
            self.exclude_semicore = self._get_default('exclude_semicore')
            self.plot_wannier_functions = self._get_default('plot_wannier_functions')
            self.retrieve_hamiltonian = self._get_default('retrieve_hamiltonian')
            self.retrieve_matrices = self._get_default('retrieve_matrices')
            self.number_of_disproj_max = self._get_default('number_of_disproj_max')
            self.number_of_disproj_min = self._get_default('number_of_disproj_min')
            self.projection_type = self._get_default('projection_type')
            self.frozen_type = self._get_default('frozen_type')
            self.energy_window_input = self._get_default('energy_window_input')
            self.compute_fermi_surface = self._get_default('compute_fermi_surface')
            self.scan_pdwf_parameter = self._get_default('scan_pdwf_parameter')
            self.nscf_kpoints_distance = self._get_default('nscf_kpoints_distance')
            self.fermi_surface_kpoint_distance = self._get_default(
                'fermi_surface_kpoint_distance'
            )
            self.compute_dhva_frequencies = self._get_default(
                'compute_dhva_frequencies'
            )
            self.dhva_starting_phi = self._get_default('dhva_starting_phi')
            self.dhva_starting_theta = self._get_default('dhva_starting_theta')
            self.dhva_ending_phi = self._get_default('dhva_ending_phi')
            self.dhva_ending_theta = self._get_default('dhva_ending_theta')
            self.dhva_num_rotation = self._get_default('dhva_num_rotation')

    def _update_kpoints_mesh(self, _=None):
        if not self.has_structure:
            mesh_grid = ''
        elif self.nscf_kpoints_distance > 0:
            mesh = create_kpoints_from_distance.process_class._func(
                self.input_structure,
                orm.Float(self.nscf_kpoints_distance),
                orm.Bool(False),
            )
            mesh_grid = f'Mesh {mesh.get_kpoints_mesh()[0]!s}'
        else:
            mesh_grid = 'Please select a number higher than 0.0'
        self._defaults['mesh_grid'] = mesh_grid
        self.mesh_grid = mesh_grid

    def _update_nscf_kpoints_distance(self):
        if self.has_pbc:
            protocol_map = {
                'balanced': 'moderate',
                'stringent': 'precise',
            }
            protocol = protocol_map.get(self.protocol, self.protocol)
            parameters = Wannier90BaseWorkChain.get_protocol_inputs(protocol=protocol)
            nscf_kpoints_distance = parameters['meta_parameters']['kpoints_distance']
        else:
            nscf_kpoints_distance = 100.0
        self._defaults['nscf_kpoints_distance'] = nscf_kpoints_distance
        self.nscf_kpoints_distance = self._defaults['nscf_kpoints_distance']
