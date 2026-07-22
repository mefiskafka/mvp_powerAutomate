"""Router de permisos — endpoints del contrato PA<->Python vía HTTP.

Dos variantes del mismo caso de uso:

* ``POST /api/v1/permits/process``          — recibe la RUTA de un PDF ya presente
  en el disco de la máquina (el escenario Power Automate Desktop local).
* ``POST /api/v1/permits/process/upload``   — recibe el PDF como multipart/form-data
  (escenario orquestador remoto; demuestra API First puro).

Ambos devuelven exactamente el mismo ``ProcessResponse``.

Códigos HTTP: los desenlaces de negocio (success y validation_error) responden
200 — son resultados válidos del proceso, no errores del servidor. Solo los
fallos técnicos (extracción imposible, render roto) responden 500. El orquestador
ramifica por el campo ``status`` del JSON, nunca por el código HTTP.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from permits.adapters.contract import to_response
from permits.application.dto.process_request import ProcessRequest
from permits.application.dto.process_response import ProcessResponse
from permits.config.container import Container
from permits.domain.entities.process_result import ProcessResult, ProcessStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/permits", tags=["permits"])


class ProcessByPathBody(BaseModel):
    """Cuerpo de la petición para procesar un PDF ya existente en disco."""

    pdf_path: str = Field(
        description="Ruta (absoluta o relativa a la raíz del proyecto) del PDF a procesar.",
        examples=["sample_data/pdfs/permiso_ejemplo.pdf"],
    )


def _get_container(request: Request) -> Container:
    return request.app.state.container


def _execute(container: Container, pdf_path: Path) -> JSONResponse:
    """Ejecuta el caso de uso y traduce el resultado a HTTP."""
    use_case = container.process_permit_use_case()
    try:
        result = use_case.execute(ProcessRequest(pdf_path=pdf_path))
    except Exception as exc:  # red de seguridad: el contrato JSON nunca se rompe
        logger.exception("Error inesperado procesando %s", pdf_path)
        result = ProcessResult(
            status=ProcessStatus.ERROR,
            message=f"Error inesperado: {exc}",
            process_id="ERROR",
            errors=[{"campo": "sistema", "regla": "inesperado", "detalle": str(exc)}],
        )
    response = to_response(result)
    http_status = 500 if result.status is ProcessStatus.ERROR else 200
    return JSONResponse(status_code=http_status, content=response.model_dump())


@router.post("/process", response_model=ProcessResponse)
def process_by_path(body: ProcessByPathBody, request: Request) -> JSONResponse:
    """Procesa un permiso a partir de la ruta de un PDF en disco."""
    return _execute(_get_container(request), Path(body.pdf_path))


@router.post("/process/upload", response_model=ProcessResponse)
async def process_by_upload(file: UploadFile, request: Request) -> JSONResponse:
    """Procesa un permiso a partir de un PDF subido como multipart/form-data."""
    suffix = Path(file.filename or "permiso.pdf").suffix or ".pdf"
    # El PDF subido se materializa en un temporal para que el extractor lo lea.
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        return _execute(_get_container(request), tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
