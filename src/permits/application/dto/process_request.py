"""DTO de entrada del caso de uso de procesamiento."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """Petición para procesar un permiso a partir de un PDF."""

    pdf_path: Path = Field(description="Ruta al PDF adjunto descargado por Power Automate")

    model_config = {"arbitrary_types_allowed": True}
