"""Entidad de dominio: ProcessResult.

Representa el desenlace de procesar un permiso de principio a fin. Es la fuente de
verdad interna que la capa de presentación traduce al contrato externo
``{status, message, output_pdf, errors}``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class ProcessStatus(StrEnum):
    """Estados posibles del procesamiento (alineados con el contrato PA↔Py)."""

    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    ERROR = "error"


@dataclass(slots=True)
class ProcessResult:
    """Resultado completo de una corrida del caso de uso."""

    status: ProcessStatus
    message: str
    process_id: str
    output_pdf: Path | None = None
    folio: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.status is ProcessStatus.SUCCESS
