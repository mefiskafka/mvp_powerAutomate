"""DTO de salida del caso de uso — es el CONTRATO con Power Automate.

Este modelo es la frontera entre el motor Python y cualquier orquestador (Power
Automate hoy, UiPath mañana). Su forma JSON es estable y está documentada en
``power_automate/FLOW.md``. Tanto la CLI (stdout) como la API (body) devuelven
exactamente esta estructura.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from permits.domain.entities.process_result import ProcessResult


class ProcessResponse(BaseModel):
    """Respuesta estandarizada del procesamiento de un permiso."""

    status: str = Field(description="success | validation_error | error")
    message: str = Field(description="Mensaje legible del resultado")
    process_id: str = Field(description="Identificador único de la corrida")
    folio: str | None = Field(default=None, description="Folio procesado, si se pudo leer")
    output_pdf: str | None = Field(
        default=None, description="Ruta absoluta del PDF generado, si aplica"
    )
    errors: list[dict[str, str]] = Field(
        default_factory=list, description="Lista de fallos de validación"
    )

    @classmethod
    def from_result(cls, result: ProcessResult) -> ProcessResponse:
        """Traduce la entidad interna ``ProcessResult`` al contrato externo."""
        return cls(
            status=result.status.value,
            message=result.message,
            process_id=result.process_id,
            folio=result.folio,
            output_pdf=str(result.output_pdf) if result.output_pdf else None,
            errors=result.errors,
        )
