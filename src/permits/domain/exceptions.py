"""Jerarquía centralizada de excepciones del dominio.

Todas las excepciones de negocio derivan de :class:`DomainError`, lo que permite
un manejo centralizado en la capa de presentación (CLI / API) y un mapeo limpio
al contrato de salida ``{status, message, errors}``.
"""

from __future__ import annotations


class DomainError(Exception):
    """Excepción base de todo el dominio.

    Attributes:
        message: Mensaje legible para humanos.
        code: Código estable para clasificar el error en integraciones.
    """

    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ExtractionError(DomainError):
    """El PDF no pudo leerse o no contiene los campos esperados."""

    code = "extraction_error"


class ValidationError(DomainError):
    """Los datos extraídos no cumplen las reglas de negocio.

    A diferencia del resto, este error transporta la lista estructurada de
    fallos de validación para poder construir el reporte de errores.
    """

    code = "validation_error"

    def __init__(self, message: str, errors: list[dict] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class PersistenceError(DomainError):
    """Fallo al leer o escribir la fuente de persistencia (Excel)."""

    code = "persistence_error"


class RenderingError(DomainError):
    """Fallo al generar el PDF resumen."""

    code = "rendering_error"


class ConfigurationError(DomainError):
    """Configuración ausente o inválida."""

    code = "configuration_error"
