"""Tests unitarios del contrato PA<->Python (mapeo de resultado y exit codes)."""

from __future__ import annotations

from pathlib import Path

from permits.adapters.contract import to_exit_code, to_response
from permits.domain.entities.process_result import ProcessResult, ProcessStatus


def test_success_maps_to_exit_0():
    result = ProcessResult(
        status=ProcessStatus.SUCCESS,
        message="ok",
        process_id="20260721-120000",
        folio="PER-1",
        output_pdf=Path("/tmp/x.pdf"),
    )
    assert to_exit_code(result) == 0
    resp = to_response(result)
    assert resp.status == "success"
    assert resp.output_pdf == "/tmp/x.pdf"


def test_validation_error_maps_to_exit_2():
    result = ProcessResult(
        status=ProcessStatus.VALIDATION_ERROR,
        message="invalido",
        process_id="20260721-120000",
        errors=[{"campo": "folio", "regla": "obligatorio", "detalle": "..."}],
    )
    assert to_exit_code(result) == 2
    assert to_response(result).errors[0]["campo"] == "folio"


def test_error_maps_to_exit_1():
    result = ProcessResult(
        status=ProcessStatus.ERROR,
        message="fallo",
        process_id="ERROR",
    )
    assert to_exit_code(result) == 1
    assert to_response(result).output_pdf is None
