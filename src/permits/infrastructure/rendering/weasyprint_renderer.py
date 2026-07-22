"""Estrategia de renderizado con WeasyPrint (Jinja2 -> HTML -> CSS -> PDF).

Produce PDFs de mayor calidad tipográfica a partir de una plantilla HTML/CSS. Es
opcional porque WeasyPrint requiere GTK/Pango instalado en el sistema operativo
(ver docs/RUNBOOK.md). La importación de ``weasyprint`` es perezosa para que el
proyecto funcione aunque la librería no esté instalada mientras se use fpdf2.
"""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.entities.validation_result import ValidationResult
from permits.domain.exceptions import RenderingError
from permits.domain.ports.pdf_renderer import PdfRenderer

logger = logging.getLogger(__name__)


class WeasyPrintRenderer(PdfRenderer):
    """Renderiza el PDF resumen con WeasyPrint y una plantilla Jinja2."""

    def __init__(self, *, templates_dir: Path, template_name: str = "summary.html.j2") -> None:
        self._templates_dir = Path(templates_dir)
        self._template_name = template_name
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(
        self,
        *,
        dto: PermitDTO,
        validation: ValidationResult,
        process_id: str,
        processed_at_iso: str,
        output_path: Path,
    ) -> Path:
        try:
            # Import perezoso: solo se exige GTK/Pango si se usa esta estrategia.
            from weasyprint import HTML  # noqa: PLC0415
        except Exception as exc:  # ImportError o fallo de librerías nativas
            raise RenderingError(
                "WeasyPrint no está disponible (requiere GTK/Pango). "
                "Usa el motor 'fpdf2' o instala WeasyPrint. Detalle: " + str(exc)
            ) from exc

        try:
            template = self._env.get_template(self._template_name)
            html_str = template.render(
                dto=dto,
                validation=validation,
                is_valid=validation.is_valid,
                issues=validation.issues,
                process_id=process_id,
                processed_at=processed_at_iso,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            HTML(string=html_str, base_url=str(self._templates_dir)).write_pdf(str(output_path))
            logger.info("PDF generado (WeasyPrint): %s", output_path)
            return output_path
        except RenderingError:
            raise
        except Exception as exc:
            raise RenderingError(f"Error generando PDF con WeasyPrint: {exc}") from exc
