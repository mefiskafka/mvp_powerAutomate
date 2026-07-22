"""Caso de uso central: ProcessPermitUseCase.

Orquesta el flujo completo de negocio, dependiendo ÚNICAMENTE de abstracciones
(puertos) inyectadas — nunca de implementaciones concretas. Esto es el corazón de
la Clean Architecture: la lógica de negocio no sabe si el PDF lo lee pdfplumber,
si la persistencia es Excel, o si el PDF lo genera WeasyPrint o fpdf2.

Flujo:
    1. Extraer datos del PDF          (PdfExtractor)
    2. Validar reglas de negocio      (PermitValidator)
    3a. Si es válido → construir entidad, persistir en Excel, generar PDF resumen.
    3b. Si es inválido → NO persistir, generar PDF de reporte de errores.
    4. Devolver ``ProcessResult`` (que la presentación traduce al contrato).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from permits.application.dto.process_request import ProcessRequest
from permits.domain.entities.permit import Permit
from permits.domain.entities.process_result import ProcessResult, ProcessStatus
from permits.domain.exceptions import DomainError, ExtractionError
from permits.domain.ports.pdf_extractor import PdfExtractor
from permits.domain.ports.pdf_renderer import PdfRenderer
from permits.domain.ports.permit_repository import PermitRepository
from permits.domain.services.permit_validator import PermitValidator

logger = logging.getLogger(__name__)


class ProcessPermitUseCase:
    """Servicio de aplicación que procesa un permiso de extremo a extremo."""

    def __init__(
        self,
        *,
        extractor: PdfExtractor,
        validator: PermitValidator,
        repository: PermitRepository,
        renderer: PdfRenderer,
        output_dir: Path,
        clock: Callable[[], datetime],
    ) -> None:
        self._extractor = extractor
        self._validator = validator
        self._repository = repository
        self._renderer = renderer
        self._output_dir = output_dir
        self._clock = clock

    def execute(self, request: ProcessRequest) -> ProcessResult:
        processed_at = self._clock()
        process_id = processed_at.strftime("%Y%m%d-%H%M%S")
        logger.info("Iniciando procesamiento %s para %s", process_id, request.pdf_path)

        # --- 1. Extracción -------------------------------------------------
        try:
            dto = self._extractor.extract(request.pdf_path)
        except ExtractionError as exc:
            logger.error("Fallo de extracción [%s]: %s", process_id, exc.message)
            return ProcessResult(
                status=ProcessStatus.ERROR,
                message=f"No se pudo extraer el permiso: {exc.message}",
                process_id=process_id,
                errors=[{"campo": "pdf", "regla": "extraccion", "detalle": exc.message}],
            )
        logger.debug("Datos extraídos [%s]: folio=%s", process_id, dto.folio)

        # --- 2. Validación -------------------------------------------------
        validation = self._validator.validate(dto)

        # --- 3. Renderizado del PDF (siempre; resumen o reporte de errores) -
        output_path = self._output_dir / f"{self._safe_folio(dto.folio)}_{process_id}.pdf"
        try:
            pdf_path = self._renderer.render(
                dto=dto,
                validation=validation,
                process_id=process_id,
                processed_at_iso=processed_at.isoformat(timespec="seconds"),
                output_path=output_path,
            )
        except DomainError as exc:
            logger.error("Fallo de renderizado [%s]: %s", process_id, exc.message)
            return ProcessResult(
                status=ProcessStatus.ERROR,
                message=f"No se pudo generar el PDF: {exc.message}",
                process_id=process_id,
                folio=dto.folio or None,
                errors=[{"campo": "pdf", "regla": "render", "detalle": exc.message}],
            )

        # --- 3a. Camino inválido: NO se persiste --------------------------
        if not validation.is_valid:
            logger.warning(
                "Permiso inválido [%s]: %d fallo(s) de validación",
                process_id,
                len(validation.issues),
            )
            return ProcessResult(
                status=ProcessStatus.VALIDATION_ERROR,
                message="El permiso no pasó las validaciones. No se actualizó el Excel.",
                process_id=process_id,
                folio=dto.folio or None,
                output_pdf=pdf_path,
                errors=validation.to_list(),
            )

        # --- 3b. Camino válido: construir entidad y persistir -------------
        permit = Permit.create(
            folio=dto.folio,
            empresa=dto.empresa,
            fecha_inicio=dto.fecha_inicio,  # type: ignore[arg-type]
            fecha_fin=dto.fecha_fin,  # type: ignore[arg-type]
            vehiculo=dto.vehiculo,
            placas=dto.placas,
            personas=dto.personas,
        )
        self._repository.save(
            permit,
            processed_at=processed_at,
            estado="PROCESADO",
            observaciones="",
        )
        logger.info("Permiso %s procesado correctamente [%s]", permit.folio, process_id)

        return ProcessResult(
            status=ProcessStatus.SUCCESS,
            message=f"Permiso {permit.folio} procesado correctamente.",
            process_id=process_id,
            folio=str(permit.folio),
            output_pdf=pdf_path,
            errors=[],
        )

    @staticmethod
    def _safe_folio(folio: str) -> str:
        """Devuelve un nombre de archivo seguro basado en el folio."""
        cleaned = "".join(c for c in (folio or "") if c.isalnum() or c in "-_")
        return cleaned or "SIN_FOLIO"
