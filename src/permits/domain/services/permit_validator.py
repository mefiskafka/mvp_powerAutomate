"""Service Layer: PermitValidator.

Concentra TODAS las reglas de negocio de validación en un único lugar (Single
Responsibility). Trabaja sobre el DTO crudo y devuelve un :class:`ValidationResult`
con la lista completa de fallos, de modo que el usuario reciba de una sola vez
todos los problemas del documento en lugar de uno a uno.

Reglas implementadas:
    1. Folio obligatorio.
    2. Empresa obligatoria.
    3. Fecha de inicio anterior a fecha de fin (ambas presentes).
    4. Placas obligatorias cuando ``vehiculo`` es verdadero.
    5. Lista de personas no vacía.
"""

from __future__ import annotations

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.entities.validation_result import ValidationResult


class PermitValidator:
    """Aplica las reglas de negocio sobre un permiso crudo."""

    def validate(self, dto: PermitDTO) -> ValidationResult:
        result = ValidationResult()

        if not dto.folio.strip():
            result.add("folio", "obligatorio", "El folio es obligatorio.")

        if not dto.empresa.strip():
            result.add("empresa", "obligatorio", "La empresa es obligatoria.")

        if dto.fecha_inicio is None or dto.fecha_fin is None:
            result.add(
                "fechas",
                "obligatorio",
                "Las fechas de inicio y fin son obligatorias.",
            )
        elif dto.fecha_inicio >= dto.fecha_fin:
            result.add(
                "fechas",
                "rango",
                (
                    f"La fecha de inicio ({dto.fecha_inicio.isoformat()}) debe ser "
                    f"anterior a la fecha de fin ({dto.fecha_fin.isoformat()})."
                ),
            )

        if dto.vehiculo and not dto.placas.strip():
            result.add(
                "placas",
                "condicional",
                "Las placas son obligatorias cuando el permiso incluye vehículo.",
            )

        if not [p for p in dto.personas if p.strip()]:
            result.add(
                "personas",
                "no_vacio",
                "Debe incluirse al menos una persona con permiso.",
            )

        return result
