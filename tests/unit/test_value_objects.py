"""Tests unitarios de los Value Objects del dominio."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from permits.domain.exceptions import ValidationError
from permits.domain.value_objects.date_range import DateRange
from permits.domain.value_objects.folio import Folio
from permits.domain.value_objects.plates import Plates


class TestFolio:
    def test_valid_folio_is_trimmed(self):
        assert Folio("  PER-001245  ").value == "PER-001245"

    def test_empty_folio_raises(self):
        with pytest.raises(ValidationError):
            Folio("   ")

    def test_invalid_characters_raise(self):
        with pytest.raises(ValidationError):
            Folio("PER 001/245")

    def test_is_immutable(self):
        folio = Folio("PER-1")
        with pytest.raises(FrozenInstanceError):
            folio.value = "OTRO"  # type: ignore[misc]


class TestDateRange:
    def test_valid_range_computes_days(self):
        rng = DateRange(date(2026, 1, 10), date(2026, 1, 15))
        assert rng.days == 5

    def test_start_after_end_raises(self):
        with pytest.raises(ValidationError):
            DateRange(date(2026, 2, 20), date(2026, 2, 10))

    def test_equal_dates_raise(self):
        with pytest.raises(ValidationError):
            DateRange(date(2026, 1, 10), date(2026, 1, 10))


class TestPlates:
    def test_normalizes_to_upper(self):
        assert Plates(" abc123 ").value == "ABC123"

    def test_empty_is_allowed(self):
        assert Plates("").is_empty is True

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError):
            Plates("!!")
