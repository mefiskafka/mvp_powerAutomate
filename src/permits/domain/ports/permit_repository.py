"""Puerto: PermitRepository (Repository Pattern).

Abstrae la persistencia del permiso. La capa de aplicación registra permisos sin
conocer que detrás hay un archivo Excel: mañana podría ser una base de datos sin
tocar el caso de uso.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from permits.domain.entities.permit import Permit


class PermitRepository(ABC):
    """Contrato de persistencia de permisos procesados."""

    @abstractmethod
    def save(
        self,
        permit: Permit,
        *,
        processed_at: datetime,
        estado: str,
        observaciones: str = "",
    ) -> None:
        """Registra un permiso procesado en el almacén.

        Raises:
            PersistenceError: si la escritura falla.
        """
        raise NotImplementedError
