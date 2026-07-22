"""Puerto: PdfRenderer (Strategy Pattern).

Abstrae la generación del PDF resumen. Existen dos estrategias concretas en
``infrastructure/rendering`` (WeasyPrint y fpdf2) seleccionables por configuración,
sin que la capa de aplicación conozca la implementación.

Recibe el DTO crudo (no la entidad ``Permit``) porque el PDF debe poder generarse
también para permisos que fallaron la validación —y que por tanto no pueden
construir una entidad válida— como reporte de errores.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.entities.validation_result import ValidationResult


class PdfRenderer(ABC):
    """Contrato para renderizar el PDF resumen de un permiso procesado."""

    @abstractmethod
    def render(
        self,
        *,
        dto: PermitDTO,
        validation: ValidationResult,
        process_id: str,
        processed_at_iso: str,
        output_path: Path,
    ) -> Path:
        """Genera el PDF resumen y devuelve la ruta escrita.

        Raises:
            RenderingError: si la generación falla.
        """
        raise NotImplementedError
