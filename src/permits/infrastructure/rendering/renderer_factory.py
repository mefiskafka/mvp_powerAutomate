"""Factory Pattern para seleccionar la estrategia de renderizado de PDF.

Traduce el valor de configuración ``pdf.renderer`` a la implementación concreta de
:class:`PdfRenderer`, aislando al contenedor de DI de los detalles de cada motor.
"""

from __future__ import annotations

from pathlib import Path

from permits.domain.exceptions import ConfigurationError
from permits.domain.ports.pdf_renderer import PdfRenderer
from permits.infrastructure.rendering.fpdf2_renderer import Fpdf2Renderer
from permits.infrastructure.rendering.weasyprint_renderer import WeasyPrintRenderer

_SUPPORTED = ("fpdf2", "weasyprint")


def create_renderer(strategy: str, *, templates_dir: Path) -> PdfRenderer:
    """Devuelve el renderer correspondiente a ``strategy``.

    Args:
        strategy: "fpdf2" (portable) o "weasyprint" (alta calidad, requiere GTK).
        templates_dir: carpeta de plantillas Jinja2 (usada por WeasyPrint).

    Raises:
        ConfigurationError: si la estrategia no está soportada.
    """
    key = (strategy or "").strip().lower()
    if key == "fpdf2":
        return Fpdf2Renderer()
    if key == "weasyprint":
        return WeasyPrintRenderer(templates_dir=templates_dir)
    raise ConfigurationError(
        f"Motor de PDF no soportado: '{strategy}'. Opciones: {', '.join(_SUPPORTED)}."
    )
