"""Check that failed child workflows produce the wrapper's declared exit codes."""

from types import SimpleNamespace

import pytest
from aiida.common.extendeddicts import AttributeDict

from aiidalab_qe_wannier90.wannier90_workchain import QeAppWannier90BandsWorkChain


@pytest.mark.parametrize(
    'method, context_key, exit_label',
    [
        ('inspect_pw_bands', 'pw_bands', 'ERROR_PW_BANDS_WORKCHAIN_FAILED'),
        ('run_optimize', 'pw_bands', 'ERROR_PW_BANDS_WORKCHAIN_FAILED'),
        ('inspect_optimize', 'wannier90_bands', 'ERROR_WANNIER90_BANDS_WORKCHAIN_FAILED'),
        ('inspect_skeaf', 'skeaf', 'ERROR_SKEAF_WORKCHAIN_FAILED'),
    ],
)
def test_failed_subworkflow_returns_declared_exit_code(method, context_key, exit_label):
    process = SimpleNamespace(
        ctx=AttributeDict({context_key: SimpleNamespace(is_finished_ok=False)}),
        exit_codes=QeAppWannier90BandsWorkChain.exit_codes,
        report=lambda message: None,
    )
    result = getattr(QeAppWannier90BandsWorkChain, method)(process)
    assert result == QeAppWannier90BandsWorkChain.exit_codes[exit_label]
