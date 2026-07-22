"""Adaptador de entrada HTTP — API First con FastAPI.

Expone el MISMO caso de uso que la CLI, con el MISMO contrato JSON
``{status, message, output_pdf, process_id, folio, errors}``. Ninguna lógica de
negocio vive aquí: este módulo solo traduce HTTP <-> caso de uso.

Ejecución:

    uvicorn permits.presentation.api.app:app --host 127.0.0.1 --port 8000

o mediante ``scripts/run_api.sh`` / ``scripts/run_api.ps1``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from permits.config.container import Container
from permits.config.settings import get_settings
from permits.presentation.api.routers import permits as permits_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Inicializa el contenedor DI y el logging una sola vez por proceso."""
    container = Container()
    container.setup_logging()
    app.state.container = container
    yield


def create_app() -> FastAPI:
    """App factory: permite crear instancias aisladas (útil en tests)."""
    settings = get_settings()
    app = FastAPI(
        title="Permits RPA API",
        description=(
            "Motor de procesamiento de permisos (API First). "
            "Power Automate Desktop u otro orquestador invoca estos endpoints "
            "y recibe el contrato estándar {status, message, output_pdf, errors}."
        ),
        version="1.0.0",
        lifespan=_lifespan,
    )
    app.include_router(permits_router.router)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        """Liveness check para el orquestador y monitoreo."""
        return {
            "status": "ok",
            "app": settings.app.name,
            "environment": settings.app.environment,
        }

    return app


app = create_app()
