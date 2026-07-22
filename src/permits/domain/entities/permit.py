"""Entidad de dominio: Permit (Permiso).

Es el agregado central del dominio. Se construye a partir de tipos primitivos
mediante :meth:`create`, que ensambla los Value Objects y por tanto aplica sus
invariantes estructurales (folio no vacío, rango de fechas coherente, formato de
placas). Las reglas que cruzan varios campos (p. ej. placas obligatorias si hay
vehículo) las evalúa el ``PermitValidator``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from permits.domain.value_objects.date_range import DateRange
from permits.domain.value_objects.folio import Folio
from permits.domain.value_objects.plates import Plates


@dataclass(slots=True)
class Permit:
    """Permiso de acceso solicitado por una empresa."""

    folio: Folio
    empresa: str
    date_range: DateRange
    vehiculo: bool
    plates: Plates
    personas: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        folio: str,
        empresa: str,
        fecha_inicio: date,
        fecha_fin: date,
        vehiculo: bool,
        placas: str,
        personas: list[str],
    ) -> Permit:
        """Fabrica un ``Permit`` a partir de primitivos, ensamblando los VOs.

        Puede lanzar :class:`ValidationError` desde los Value Objects si algún
        campo estructural es inválido.
        """
        return cls(
            folio=Folio(folio),
            empresa=(empresa or "").strip(),
            date_range=DateRange(fecha_inicio, fecha_fin),
            vehiculo=vehiculo,
            plates=Plates(placas),
            personas=[p.strip() for p in personas if p and p.strip()],
        )

    @property
    def cantidad_personas(self) -> int:
        return len(self.personas)
