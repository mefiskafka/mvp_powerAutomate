"""Value Object: Rango de fechas del permiso.

Encapsula la invariante "fecha_inicio < fecha_fin". Construir un rango inválido
es imposible, por lo que el resto del dominio puede confiar en su validez.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from permits.domain.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class DateRange:
    """Intervalo cerrado ``[start, end]`` con ``start`` estrictamente menor a ``end``."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValidationError(
                f"La fecha de inicio ({self.start.isoformat()}) debe ser anterior "
                f"a la fecha de fin ({self.end.isoformat()})."
            )

    @property
    def days(self) -> int:
        """Número de días que abarca el permiso."""
        return (self.end - self.start).days
