"""DTO: PermitDTO.

Objeto de transferencia entre capas. Representa los datos *crudos* extraídos del
PDF, antes de validarse o convertirse en la entidad de dominio. Es un modelo
Pydantic para validación de tipos y (de)serialización JSON, que es justamente el
formato del contrato con Power Automate.

Nota de diseño: el DTO NO impone reglas de negocio (fechas coherentes, placas
obligatorias, etc.). Eso es responsabilidad del ``PermitValidator``, para poder
acumular y reportar TODOS los errores a la vez en lugar de fallar en el primero.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PermitDTO(BaseModel):
    """Datos crudos de un permiso tal como se extraen del documento."""

    folio: str = Field(default="", description="Folio del permiso, p. ej. PER-001245")
    empresa: str = Field(default="", description="Nombre de la compañía solicitante")
    fecha_inicio: date | None = Field(default=None, description="Inicio de vigencia")
    fecha_fin: date | None = Field(default=None, description="Fin de vigencia")
    vehiculo: bool = Field(default=False, description="¿Incluye vehículo?")
    placas: str = Field(default="", description="Placas del vehículo, si aplica")
    personas: list[str] = Field(default_factory=list, description="Personas con permiso")

    model_config = {"str_strip_whitespace": True}
