"""Tests de integración del caso de uso ProcessPermitUseCase con dobles de prueba."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from permits.application.dto.permit_dto import PermitDTO
from permits.application.dto.process_request import ProcessRequest
from permits.application.use_cases.process_permit import ProcessPermitUseCase
from permits.domain.entities.process_result import ProcessStatus
from permits.domain.services.permit_validator import PermitValidator
from tests.conftest import FakeExtractor


def _use_case(dto, repo, renderer, clock, tmp_path: Path) -> ProcessPermitUseCase:
    return ProcessPermitUseCase(
        extractor=FakeExtractor(dto),
        validator=PermitValidator(),
        repository=repo,
        renderer=renderer,
        output_dir=tmp_path,
        clock=clock,
    )


def test_valid_permit_persists_and_renders(
    valid_dto, in_memory_repo, fake_renderer, fixed_clock, tmp_path
):
    uc = _use_case(valid_dto, in_memory_repo, fake_renderer, fixed_clock, tmp_path)
    result = uc.execute(ProcessRequest(pdf_path=tmp_path / "x.pdf"))

    assert result.status is ProcessStatus.SUCCESS
    assert result.process_id == "20260721-120000"
    assert len(in_memory_repo.saved) == 1
    assert in_memory_repo.saved[0]["folio"] == "PER-001245"
    assert result.output_pdf is not None and result.output_pdf.exists()


def test_invalid_permit_does_not_persist(
    in_memory_repo, fake_renderer, fixed_clock, tmp_path
):
    invalid = PermitDTO(
        folio="PER-2",
        empresa="ACME",
        fecha_inicio=date(2026, 2, 20),
        fecha_fin=date(2026, 2, 10),  # inicio > fin
        vehiculo=True,
        placas="",  # falta placa
        personas=["Pedro"],
    )
    uc = _use_case(invalid, in_memory_repo, fake_renderer, fixed_clock, tmp_path)
    result = uc.execute(ProcessRequest(pdf_path=tmp_path / "x.pdf"))

    assert result.status is ProcessStatus.VALIDATION_ERROR
    assert in_memory_repo.saved == []  # NO se tocó el "Excel"
    assert len(result.errors) == 2
    # Aun así se genera el PDF de reporte de errores.
    assert result.output_pdf is not None and result.output_pdf.exists()


def test_pdf_generated_for_both_paths(
    valid_dto, in_memory_repo, fake_renderer, fixed_clock, tmp_path
):
    uc = _use_case(valid_dto, in_memory_repo, fake_renderer, fixed_clock, tmp_path)
    uc.execute(ProcessRequest(pdf_path=tmp_path / "x.pdf"))
    assert fake_renderer.calls and fake_renderer.calls[0]["is_valid"] is True
