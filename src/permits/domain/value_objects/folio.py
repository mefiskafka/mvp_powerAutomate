"""Value Object: Folio de permiso.

Un Value Object es inmutable y se define por su valor, no por identidad. Encapsula
la invariante "un folio no puede estar vacío" para que sea imposible construir un
folio inválido dentro del dominio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from permits.domain.exceptions import ValidationError

_FOLIO_PATTERN = re.compile(r"^[A-Za-z0-9\-]+$")


@dataclass(frozen=True, slots=True)
class Folio:
    """Identificador de negocio de un permiso (p. ej. ``PER-001245``)."""

    value: str

    def __post_init__(self) -> None:
        value = (self.value or "").strip()
        if not value:
            raise ValidationError("El folio es obligatorio y no puede estar vacío.")
        if not _FOLIO_PATTERN.match(value):
            raise ValidationError(
                f"El folio '{value}' contiene caracteres inválidos "
                "(solo letras, números y guiones)."
            )
        # Normaliza a la versión saneada sin romper la inmutabilidad.
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value
