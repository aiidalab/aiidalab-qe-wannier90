"""Wannier90 results view widgets"""

from aiidalab_qe.common.bands_pdos import BandsPdosModel, BandsPdosWidget
from aiidalab_qe.common.panel import ResultsPanel
import ipywidgets as ipw
from .model import Wannier90ResultsModel
from .utils import create_download_link, plot_skeaf
from table_widget import TableWidget
import plotly.graph_objs as go
import plotly.express as px
from weas_widget import WeasWidget
import ast
import numpy as np

# Define a threshold for considering atoms "almost equally distant"
DISTANCE_THRESHOLD = 0.01
BAND_DISTANCE_WARNING_MEV = 10.0  # show warning if distance exceeds this threshold (in meV)

ISOSURFACE_COLOR = {
    'positive': [1.0, 1.0, 0.0, 0.8],
    'negative': [0.0, 1.0, 1.0, 0.8],
}

class Wannier90ResultsPanel(ResultsPanel[Wannier90ResultsModel]):

    def _render(self):
        """Render the Wannier90 results panel."""
        self._model.fetch_result()

        # Retrieve band structures
        pw_bands, wannier90_bands = self._model.get_bands_node()
        wannier90_bands['trace_settings'] = {'dash': 'dash',
                                             'shape': 'linear',
                                             'color': 'red'}
        model = BandsPdosModel(
            bands=pw_bands,
            external_bands={'Wannier-interpolated bands': wannier90_bands},
            plot_settings={'bands_trace_settings': {'name': 'DFT bands'}},
        )

        # Create and render the bands/PDOS widget
        bands_widget = BandsPdosWidget(model=model)
        bands_widget.render()

        # Wannier90 outputs summary (merged with bands distance)
        wannier90_outputs = self._model.wannier90_outputs
        bands_distance = self._model.bands_distance
        omega_tot = (
            wannier90_outputs['Omega_D']
            + wannier90_outputs['Omega_I']
            + wannier90_outputs['Omega_OD']
        )

        # Yellow warning if bands distance > 10 meV
        bands_distance_warning_widget = ipw.HTML()
        bands_distance_mev = bands_distance * 1000.0

        wannier90_outputs_parameters = ipw.HTML(
            f"""
            <div style="margin-top:10px; padding:15px;">
            <table style="width:60%; border-collapse:collapse; text-align:left; font-size:14px;">
                <tr>
                    <td><b>Number of WFs:</b></td>
                    <td>{wannier90_outputs['number_wfs']}</td>
                </tr>
                <tr>
                    <td><b>Total spread Ω<sub>tot</sub>:</b></td>
                    <td>{omega_tot:.3f} Å²</td>
                </tr>
                <tr>
                    <td><b>Components of the spread:</b></td>
                    <td>
                        Ω<sub>D</sub>: {wannier90_outputs['Omega_D']:.3f} Å² &nbsp;&nbsp;
                        Ω<sub>I</sub>: {wannier90_outputs['Omega_I']:.3f} Å² &nbsp;&nbsp;
                        Ω<sub>OD</sub>: {wannier90_outputs['Omega_OD']:.3f} Å²
                    </td>
                </tr>
                <tr>
                    <td><b>Band distance:</b></td>
                    <td>{bands_distance_mev:.3f} meV</td>
                </tr>
            </table>
            </div>
            """
        )
        show_bands_distance_warning = False
        if bands_distance_mev > BAND_DISTANCE_WARNING_MEV:
            show_bands_distance_warning = True
            bands_distance_warning_widget.value = f"""
            <div style="
                margin: 12px 0;
                padding: 12px 14px;
                border: 1px solid #f1c40f;
                background: #fff8db;
                color: #7a5f00;
                border-radius: 8px;
                font-size: 14px;
                line-height: 1.4;
            ">
                <strong>Warning:</strong>
                Current bands distance: {bands_distance_mev:.3f} meV > 10 meV.
                Considering rerunning this workflow by activating
                <em>Exhaustive PDWF parameters scan</em>, in the
                settings panel of the Wannier90 plugin (step 2), if you have not already done so.
                <br>
            </div>
            """

        # Omega convergence plots
        omega_is = self._model.omega_is
        fig = px.line(
            x=range(len(omega_is)), y=omega_is,
            title='Convergence of Ωᵢ'
        )
        fig.update_yaxes(title='Ωᵢ')
        fig.update_xaxes(title='Number of iterations')
        self.plot_omega_is = go.FigureWidget(fig)

        omega_tots = self._model.omega_tots
        fig = px.line(
            x=range(len(omega_tots)), y=omega_tots,
            title='Convergence of Ωₜₒₜ'
        )
        fig.update_yaxes(title='Ωₜₒₜ')
        fig.update_xaxes(title='Number of iterations')
        self.plot_omega_tots = go.FigureWidget(fig)

        # Structure
        self.structure_viewer = WeasWidget()
        atoms = self._model.structure.get_ase()
        self.structure_viewer.from_ase(atoms)
        self.structure_viewer.avr.model_style = 1
        self.structure_viewer.avr.color_type = 'VESTA'
        self.structure_viewer.avr.boundary = [[-0.05, 1.05], [-0.05, 1.05], [-0.05, 1.05]]

        # Isosurface
        self.isosurface_data = self._model.get_isosurface() or {'parameters': {}, 'mesh_data': {}}

        structure_viewer_section = ipw.VBox([
            ipw.HTML('<h3>Structure</h3>'),
            self.structure_viewer,
        ], layout=ipw.Layout(width='50%', margin='10px 0'))

        # Wannier centers and spreads table
        self.table = TableWidget(style={'margin-top': '10px'})
        self.table.from_data(
            self._model.wannier_centers_spreads['data'],
            columns=self._model.wannier_centers_spreads['columns']
        )
        self.table.observe(self.on_single_row_select, 'selectedRowId')
        self.table_description = ipw.HTML(
            'Click on a table row to visualize on the right the corresponding Wannier function in real space.'
        )
        table_section = ipw.VBox([
            ipw.HTML('<h3>Wannier centers and spreads</h3>'),
            self.table_description,
            self.table
        ], layout=ipw.Layout(width='50%', margin='10px 0'))

        self.skeaf_container = ipw.VBox([
            ipw.HTML('<h2>Fermi surface</h2>'),
            ipw.HTML('<h3>de Haas van Alphen (dHva) frequencies</h3>'),
        ])

        # de Haas van Alphen (dHvA) frequencies
        skeaf_data = self._model.get_skeaf()  # dictionary {band: frequency_array}
        if skeaf_data is not None:
            self.plot_skeaf = plot_skeaf(skeaf_data)
            self.skeaf_container.children += (self.plot_skeaf,)
        else:
            # hide the skeaf container if no data is available
            self.skeaf_container.layout.display = 'none'

        # Downloads section
        download_links = []
        for filename in self._model.retrieved.list_object_names():
            if filename.endswith('_tb.dat'):
                temp_dir = self._model.retrieved
                download_links.append(create_download_link(
                    temp_dir, filename, description=f'Download the tight-binding model {filename}'
                ))
            elif filename.endswith('.bxsf'):
                temp_dir = self._model.retrieved
                download_links.append(create_download_link(
                    temp_dir, filename, description=f'Download the Fermi surface {filename}'
                ))

        # Arrange components in the panel
        self.children = [
            ipw.VBox([
                ipw.HTML('<h2>DFT and Wannier-interpolated electronic band structure</h2>'),
                bands_widget,
            ]),
            ipw.VBox([
                ipw.HTML('<h2>Wannierization details</h2>'),
                wannier90_outputs_parameters,
                bands_distance_warning_widget if show_bands_distance_warning else ipw.HTML(''),
                ipw.HBox([self.plot_omega_is, self.plot_omega_tots]),
                ipw.HBox([structure_viewer_section, table_section]),
            ]),
            self.skeaf_container,
            ipw.VBox([
                ipw.HTML('<h2>Download files</h2>'),
                ipw.VBox(download_links),
            ]),
        ]

    def on_single_row_select(self, change):
        id = change.get('new')
        if id is None:
            return

        # Get center for the selected row
        try:
            center_str = next(row['centers_final'] for row in self.table.data if row['id'] == id)
            center = ast.literal_eval(center_str)
        except StopIteration:
            return
        except Exception:
            # Fallback if parsing fails
            return

        atoms = self._model.structure.get_ase()
        positions = atoms.get_positions()
        distances = np.linalg.norm(positions - center, axis=1)

        # Find minimum distance and atoms within threshold
        min_distance = float(np.min(distances))
        indices = np.where(np.abs(distances - min_distance) < DISTANCE_THRESHOLD)[0]
        self.structure_viewer.avr.selected_atoms_indices = indices.tolist()

        key = f'aiida_{int(id):05d}'
        data = []

        params = self.isosurface_data.get('parameters', {})
        mesh = self.isosurface_data.get('mesh_data', {})

        if key in params and 'isovalue' in params[key]:
            for item in ['positive', 'negative']:
                try:
                    vertices = mesh[f'{key}_{item}_vertices'].value.tolist()
                    faces = mesh[f'{key}_{item}_faces'].value.tolist()
                except KeyError:
                    continue
                data.append({
                    'name': item,
                    'color': ISOSURFACE_COLOR[item],
                    'material': 'Standard',
                    'position': [0, 0.0, 0.0],
                    'vertices': vertices,
                    'faces': faces,
                })

        self.structure_viewer.any_mesh.settings = data
