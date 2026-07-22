"""Contenedor de Inyección de Dependencias (DI manual).

Ensambla el grafo de objetos: crea las implementaciones concretas de infraestructura
y las inyecta en el caso de uso. Es el ÚNICO lugar del código donde la capa de
aplicación se conecta con la infraestructura. Cambiar de motor de PDF, de repositorio
o de extractor se hace aquí, sin tocar la lógica de negocio.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from permits.application.use_cases.process_permit import ProcessPermitUseCase
from permits.config.settings import Settings, get_settings
from permits.domain.services.permit_validator import PermitValidator
from permits.infrastructure.extraction.pdfplumber_extractor import PdfplumberExtractor
from permits.infrastructure.logging.logger import configure_logging
from permits.infrastructure.persistence.excel_permit_repository import ExcelPermitRepository
from permits.infrastructure.rendering.renderer_factory import create_renderer


class Container:
    """Composición de dependencias de la aplicación."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._clock = clock or datetime.now
        self._logging_configured = False

    @property
    def settings(self) -> Settings:
        return self._settings

    def setup_logging(self) -> None:
        if self._logging_configured:
            return
        cfg = self._settings.logging
        configure_logging(
            logs_dir=self._settings.logs_dir,
            level=cfg.level,
            file_prefix=cfg.file_prefix,
            console=cfg.console,
        )
        self._logging_configured = True

    def process_permit_use_case(self) -> ProcessPermitUseCase:
        s = self._settings
        return ProcessPermitUseCase(
            extractor=PdfplumberExtractor(),
            validator=PermitValidator(),
            repository=ExcelPermitRepository(
                excel_path=s.excel_path,
                sheet_name=s.excel.sheet_name,
                headers=s.excel.headers,
            ),
            renderer=create_renderer(s.pdf.renderer, templates_dir=s.templates_dir),
            output_dir=s.output_dir,
            clock=self._clock,
        )
