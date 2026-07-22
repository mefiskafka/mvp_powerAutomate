"""Fixtures compartidas y dobles de prueba (fakes) para los tests."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.entities.permit import Permit
from permits.domain.ports.pdf_extractor import PdfExtractor
from permits.domain.ports.pdf_renderer import PdfRenderer
from permits.domain.ports.permit_repository import PermitRepository

FIXED_NOW = datetime(2026, 7, 21, 12, 0, 0)


@pytest.fixture
def fixed_clock():
    return lambda: FIXED_NOW


@pytest.fixture
def valid_dto() -> PermitDTO:
    return PermitDTO(
        folio="PER-001245",
        empresa="Spin",
        fecha_inicio=date(2026, 1, 10),
        fecha_fin=date(2026, 1, 15),
        vehiculo=True,
        placas="ABC123",
        personas=["Juan Perez", "Maria Lopez"],
    )


class FakeExtractor(PdfExtractor):
    """Devuelve un DTO predefinido, ignorando el PDF real."""

    def __init__(self, dto: PermitDTO) -> None:
        self._dto = dto

    def extract(self, pdf_path: Path) -> PermitDTO:  # noqa: ARG002
        return self._dto


class InMemoryRepository(PermitRepository):
    """Repositorio en memoria para verificar la persistencia sin Excel."""

    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(self, permit: Permit, *, processed_at, estado, observaciones="") -> None:
        self.saved.append(
            {
                "folio": str(permit.folio),
                "empresa": permit.empresa,
                "estado": estado,
                "processed_at": processed_at,
            }
        )


class FakeRenderer(PdfRenderer):
    """Escribe un archivo trivial y registra las llamadas."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def render(self, *, dto, validation, process_id, processed_at_iso, output_path: Path) -> Path:
        self.calls.append({"process_id": process_id, "is_valid": validation.is_valid})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"%PDF-fake")
        return output_path


@pytest.fixture
def fake_renderer() -> FakeRenderer:
    return FakeRenderer()


@pytest.fixture
def in_memory_repo() -> InMemoryRepository:
    return InMemoryRepository()
