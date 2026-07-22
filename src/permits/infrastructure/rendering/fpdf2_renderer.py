"""Estrategia de renderizado con fpdf2 (pure-Python, sin dependencias del SO).

Es el motor por defecto: garantiza que el proyecto genere PDFs en cualquier
máquina (Windows/Linux/macOS) sin instalar GTK/Pango. Produce el PDF resumen con
la información del permiso, el resultado de las validaciones, la fecha de
procesamiento y el número de proceso.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fpdf import FPDF

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.entities.validation_result import ValidationResult
from permits.domain.exceptions import RenderingError
from permits.domain.ports.pdf_renderer import PdfRenderer

logger = logging.getLogger(__name__)

_OK_COLOR = (21, 128, 61)  # verde
_ERR_COLOR = (185, 28, 28)  # rojo
_MUTED = (100, 100, 100)


class Fpdf2Renderer(PdfRenderer):
    """Renderiza el PDF resumen usando fpdf2."""

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
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            self._header(pdf, validation.is_valid)
            self._meta(pdf, process_id, processed_at_iso)
            self._permit_info(pdf, dto)
            self._validation_section(pdf, validation)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(output_path))
            logger.info("PDF generado (fpdf2): %s", output_path)
            return output_path
        except Exception as exc:
            raise RenderingError(f"Error generando PDF con fpdf2: {exc}") from exc

    # ------------------------------------------------------------------ #
    def _header(self, pdf: FPDF, is_valid: bool) -> None:
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "Resumen de Procesamiento de Permiso", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 12)
        if is_valid:
            pdf.set_text_color(*_OK_COLOR)
            pdf.cell(0, 8, "Estado: PROCESADO CORRECTAMENTE", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_text_color(*_ERR_COLOR)
            pdf.cell(0, 8, "Estado: RECHAZADO POR VALIDACIONES", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def _meta(self, pdf: FPDF, process_id: str, processed_at_iso: str) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*_MUTED)
        pdf.cell(0, 6, f"Numero de proceso: {process_id}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Fecha de procesamiento: {processed_at_iso}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    def _permit_info(self, pdf: FPDF, dto: PermitDTO) -> None:
        self._section_title(pdf, "Informacion del permiso")
        rows = [
            ("Folio", dto.folio or "-"),
            ("Empresa", dto.empresa or "-"),
            ("Fecha inicio", dto.fecha_inicio.isoformat() if dto.fecha_inicio else "-"),
            ("Fecha fin", dto.fecha_fin.isoformat() if dto.fecha_fin else "-"),
            ("Vehiculo", "Si" if dto.vehiculo else "No"),
            ("Placas", dto.placas or "-"),
            ("Cantidad de personas", str(len(dto.personas))),
        ]
        pdf.set_font("Helvetica", "", 11)
        for label, value in rows:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(55, 7, f"{label}:", new_x="RIGHT", new_y="TOP")
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

        if dto.personas:
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Personas:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            for persona in dto.personas:
                pdf.cell(6)
                pdf.cell(0, 6, f"- {persona}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    def _validation_section(self, pdf: FPDF, validation: ValidationResult) -> None:
        self._section_title(pdf, "Resultado de validaciones")
        if validation.is_valid:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(*_OK_COLOR)
            pdf.cell(0, 7, "Todas las validaciones se cumplieron.", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            return

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*_ERR_COLOR)
        pdf.cell(
            0, 7, f"Se encontraron {len(validation.issues)} error(es):",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)
        for issue in validation.issues:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"- [{issue.campo}] {issue.regla}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(6)
            pdf.multi_cell(0, 6, issue.detalle, new_x="LMARGIN", new_y="NEXT")

    def _section_title(self, pdf: FPDF, title: str) -> None:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(235, 235, 235)
        pdf.cell(0, 8, f"  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(2)
