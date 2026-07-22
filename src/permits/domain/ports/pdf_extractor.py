"""Puerto: PdfExtractor.

Interfaz (Dependency Inversion) que abstrae la extracción de datos de un PDF. La
capa de aplicación depende de esta abstracción, no de ``pdfplumber``. La
implementación concreta vive en ``infrastructure/extraction``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from permits.application.dto.permit_dto import PermitDTO


class PdfExtractor(ABC):
    """Contrato para extraer un :class:`PermitDTO` a partir de un PDF."""

    @abstractmethod
    def extract(self, pdf_path: Path) -> PermitDTO:
        """Lee el PDF y devuelve los datos crudos como DTO.

        Raises:
            ExtractionError: si el PDF no puede leerse o faltan campos clave.
        """
        raise NotImplementedError
