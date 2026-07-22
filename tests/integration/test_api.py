"""Tests de integración del adaptador FastAPI (mismo contrato que la CLI)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from permits.presentation.api.app import create_app


def _make_pdf(path: Path, lines: list[str]) -> Path:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    for line in lines:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))
    return path


VALID_LINES = [
    "Solicitud de Permiso",
    "Folio: PER-API-1",
    "Empresa: Spin",
    "Fecha Inicio: 2026-03-01",
    "Fecha Fin: 2026-03-05",
    "Vehiculo: No",
    "Placas:",
    "Personas con permiso:",
    "- Carla Ruiz",
]

INVALID_LINES = [
    "Solicitud de Permiso",
    "Folio:",
    "Empresa:",
    "Fecha Inicio: 2026-03-05",
    "Fecha Fin: 2026-03-01",
    "Vehiculo: Si",
    "Placas:",
]


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient con salidas redirigidas a un directorio temporal.

    Sin esto, los tests escribirían PDFs reales en sample_data/expected_output
    y filas en data/permisos.xlsx (contaminando el repositorio).
    """
    from permits.config.settings import get_settings

    monkeypatch.setenv("PERMITS_PATHS__OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("PERMITS_PATHS__EXCEL_FILE", str(tmp_path / "permisos.xlsx"))
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:  # `with` dispara el lifespan
            yield client
    finally:
        get_settings.cache_clear()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_process_by_path_success(client, tmp_path):
    pdf = _make_pdf(tmp_path / "ok.pdf", VALID_LINES)
    resp = client.post("/api/v1/permits/process", json={"pdf_path": str(pdf)})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["folio"] == "PER-API-1"
    assert body["output_pdf"] and Path(body["output_pdf"]).exists()
    assert body["errors"] == []


def test_process_by_path_validation_error(client, tmp_path):
    pdf = _make_pdf(tmp_path / "bad.pdf", INVALID_LINES)
    resp = client.post("/api/v1/permits/process", json={"pdf_path": str(pdf)})

    assert resp.status_code == 200  # desenlace de negocio, no error de servidor
    body = resp.json()
    assert body["status"] == "validation_error"
    campos = {e["campo"] for e in body["errors"]}
    assert {"folio", "empresa", "placas"}.issubset(campos)


def test_process_missing_pdf_is_error(client):
    resp = client.post("/api/v1/permits/process", json={"pdf_path": "no/existe.pdf"})
    assert resp.status_code == 500
    assert resp.json()["status"] == "error"


def test_process_by_upload_success(client, tmp_path):
    pdf = _make_pdf(tmp_path / "up.pdf", VALID_LINES)
    with pdf.open("rb") as fh:
        resp = client.post(
            "/api/v1/permits/process/upload",
            files={"file": ("permiso.pdf", fh, "application/pdf")},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_cli_and_api_share_contract_shape(client, tmp_path):
    """El JSON del API debe tener exactamente las claves del contrato."""
    pdf = _make_pdf(tmp_path / "ok.pdf", VALID_LINES)
    body = client.post("/api/v1/permits/process", json={"pdf_path": str(pdf)}).json()
    assert set(body) == {"status", "message", "process_id", "folio", "output_pdf", "errors"}
