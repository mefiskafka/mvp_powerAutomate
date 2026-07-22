"""Value Object: Placas de vehículo.

Modela las placas como valor opcional. La regla "placas obligatorias cuando el
permiso incluye vehículo" es una regla de negocio de nivel superior y vive en el
:class:`~permits.domain.services.permit_validator.PermitValidator`, no aquí, porque
depende de otro campo del permiso (``vehiculo``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from permits.domain.exceptions import ValidationError

_PLATES_PATTERN = re.compile(r"^[A-Za-z0-9\- ]{3,15}$")


@dataclass(frozen=True, slots=True)
class Plates:
    """Placa vehicular normalizada (mayúsculas, sin espacios sobrantes)."""

    value: str

    def __post_init__(self) -> None:
        value = (self.value or "").strip().upper()
        if value and not _PLATES_PATTERN.match(value):
            raise ValidationError(f"El formato de las placas '{value}' es inválido.")
        object.__setattr__(self, "value", value)

    @property
    def is_empty(self) -> bool:
        return self.value == ""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value
