"""Tests unitarios del servicio de reglas de negocio PermitValidator."""

from __future__ import annotations

from datetime import date

import pytest

from permits.application.dto.permit_dto import PermitDTO
from permits.domain.services.permit_validator import PermitValidator


@pytest.fixture
def validator() -> PermitValidator:
    return PermitValidator()


def _base_dto(**overrides) -> PermitDTO:
    data = dict(
        folio="PER-1",
        empresa="Spin",
        fecha_inicio=date(2026, 1, 10),
        fecha_fin=date(2026, 1, 15),
        vehiculo=False,
        placas="",
        personas=["Juan Perez"],
    )
    data.update(overrides)
    return PermitDTO(**data)


def test_valid_permit_has_no_issues(validator):
    result = validator.validate(_base_dto())
    assert result.is_valid


def test_missing_folio(validator):
    result = validator.validate(_base_dto(folio=""))
    assert not result.is_valid
    assert any(i.campo == "folio" for i in result.issues)


def test_missing_empresa(validator):
    result = validator.validate(_base_dto(empresa="  "))
    assert any(i.campo == "empresa" for i in result.issues)


def test_start_after_end(validator):
    result = validator.validate(
        _base_dto(fecha_inicio=date(2026, 2, 20), fecha_fin=date(2026, 2, 10))
    )
    assert any(i.campo == "fechas" and i.regla == "rango" for i in result.issues)


def test_vehicle_without_plates(validator):
    result = validator.validate(_base_dto(vehiculo=True, placas=""))
    assert any(i.campo == "placas" for i in result.issues)


def test_vehicle_with_plates_is_ok(validator):
    result = validator.validate(_base_dto(vehiculo=True, placas="ABC123"))
    assert result.is_valid


def test_empty_personas(validator):
    result = validator.validate(_base_dto(personas=[]))
    assert any(i.campo == "personas" for i in result.issues)


def test_accumulates_multiple_errors(validator):
    result = validator.validate(
        _base_dto(folio="", empresa="", vehiculo=True, placas="", personas=[])
    )
    campos = {i.campo for i in result.issues}
    assert {"folio", "empresa", "placas", "personas"}.issubset(campos)
