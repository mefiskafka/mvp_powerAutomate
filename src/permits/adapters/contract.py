"""Contrato de integración Power Automate <-> Python.

Centraliza la traducción entre el resultado interno (:class:`ProcessResult`) y los
artefactos que consume el orquestador:

    * el JSON de respuesta (idéntico en CLI y API), y
    * el código de salida del proceso (para que Power Automate ramifique fácil).

Mantener este mapeo en un solo lugar es lo que permite reemplazar Power Automate
por UiPath sin tocar el núcleo: solo cambia quien lee este contrato.
"""

from __future__ import annotations

from permits.application.dto.process_response import ProcessResponse
from permits.domain.entities.process_result import ProcessResult, ProcessStatus

# Códigos de salida de la CLI por estado.
EXIT_CODES: dict[ProcessStatus, int] = {
    ProcessStatus.SUCCESS: 0,
    ProcessStatus.VALIDATION_ERROR: 2,
    ProcessStatus.ERROR: 1,
}


def to_response(result: ProcessResult) -> ProcessResponse:
    """Convierte el resultado de dominio al DTO de contrato (JSON)."""
    return ProcessResponse.from_result(result)


def to_exit_code(result: ProcessResult) -> int:
    """Devuelve el código de salida asociado al estado del resultado."""
    return EXIT_CODES.get(result.status, 1)
