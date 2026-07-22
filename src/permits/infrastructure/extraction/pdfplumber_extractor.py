"""Implementación de PdfExtractor con pdfplumber.

Lee el texto del PDF y lo interpreta con un parser basado en etiquetas
(``Etiqueta: valor``), tolerante a acentos y variantes de mayúsculas. Está
deliberadamente aislado en infraestructura: es el único módulo que conoce
``pdfplumber`` y el formato concreto del documento.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from pathlib import Path

import pdfplumber

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.exceptions import ExtractionError
from permits.domain.ports.pdf_extractor import PdfExtractor

logger = logging.getLogger(__name__)

# Etiquetas aceptadas por campo (en minúsculas, sin acentos-sensibilidad).
_LABELS = {
    "folio": ("folio",),
    "empresa": ("empresa", "compañia", "compania", "compañía"),
    "fecha_inicio": ("fecha inicio", "fecha de inicio"),
    "fecha_fin": ("fecha fin", "fecha de fin", "fecha final"),
    "vehiculo": ("vehiculo", "vehículo"),
    "placas": ("placas", "placa"),
}

_TRUE_VALUES = {"si", "sí", "true", "1", "x", "yes"}
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


class PdfplumberExtractor(PdfExtractor):
    """Extrae un :class:`PermitDTO` de un PDF de solicitud de permiso."""

    def extract(self, pdf_path: Path) -> PermitDTO:
        path = Path(pdf_path)
        if not path.is_file():
            raise ExtractionError(f"El PDF no existe: {path}")

        try:
            text = self._read_text(path)
        except Exception as exc:  # pdfplumber puede lanzar varios tipos
            raise ExtractionError(f"No se pudo leer el PDF: {exc}") from exc

        if not text.strip():
            raise ExtractionError("El PDF no contiene texto legible.")

        fields = self._parse_labeled_fields(text)
        personas = self._parse_personas(text)

        return PermitDTO(
            folio=fields.get("folio", ""),
            empresa=fields.get("empresa", ""),
            fecha_inicio=self._parse_date(fields.get("fecha_inicio")),
            fecha_fin=self._parse_date(fields.get("fecha_fin")),
            vehiculo=self._parse_bool(fields.get("vehiculo")),
            placas=fields.get("placas", ""),
            personas=personas,
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _read_text(path: Path) -> str:
        parts: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts)

    @staticmethod
    def _parse_labeled_fields(text: str) -> dict[str, str]:
        found: dict[str, str] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if ":" not in line:
                continue
            label, _, value = line.partition(":")
            label_norm = label.strip().lower()
            value = value.strip()
            for field, aliases in _LABELS.items():
                if field in found:
                    continue
                if any(label_norm == alias for alias in aliases):
                    found[field] = value
                    break
        return found

    @staticmethod
    def _parse_personas(text: str) -> list[str]:
        """Extrae la lista de personas.

        Reconoce una sección iniciada por una línea que contiene "personas" y
        recolecta las viñetas siguientes (``- Nombre`` o ``• Nombre``).
        """
        personas: list[str] = []
        collecting = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if "personas" in line.lower() and ":" in line:
                collecting = True
                # Soporta "Personas: Juan, Maria" en una sola línea.
                _, _, inline = line.partition(":")
                inline = inline.strip()
                if inline:
                    personas.extend(_split_names(inline))
                continue
            if collecting:
                match = re.match(r"^[\-•\*]\s*(.+)$", line)
                if match:
                    personas.append(match.group(1).strip())
                elif re.match(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ]", line):
                    # Nombre sin viñeta bajo la sección.
                    personas.append(line)
                else:
                    collecting = False
        return [p for p in personas if p]

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        logger.warning("Fecha no reconocida: %r", value)
        return None

    @staticmethod
    def _parse_bool(value: str | None) -> bool:
        if not value:
            return False
        return value.strip().lower() in _TRUE_VALUES


def _split_names(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;]", text) if part.strip()]
