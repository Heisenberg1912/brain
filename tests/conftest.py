"""Shared fixtures for tests."""
import pytest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace


@pytest.fixture
def sample_weights():
    """Standard scoring weights matching scoring_weights.json."""
    return {
        "land_value": {
            "avg_price_normalized": 0.30,
            "infra_proximity": 0.25,
            "zoning_favorability": 0.20,
            "density": 0.15,
            "price_trend": 0.10,
        },
        "development_potential": {
            "fsi_headroom": 0.30,
            "zoning_type_value": 0.25,
            "infra_planned": 0.25,
            "price_growth_rate": 0.20,
        },
        "future_appreciation": {
            "price_trend_5yr": 0.25,
            "infra_pipeline": 0.30,
            "population_growth": 0.20,
            "zoning_shift_potential": 0.25,
        },
    }


@pytest.fixture
def make_infra():
    """Factory for mock infrastructure items."""
    def _make(infra_type="metro_station", status="operational", distance_km=1.0):
        return {
            "infrastructure": SimpleNamespace(infra_type=infra_type, status=status, name=f"Test {infra_type}"),
            "distance_km": distance_km,
        }
    return _make


@pytest.fixture
def make_price():
    """Factory for mock PropertyPrice objects."""
    def _make(price_per_sqft, recorded_date_str):
        return SimpleNamespace(
            price_per_sqft=Decimal(str(price_per_sqft)),
            recorded_date=date.fromisoformat(recorded_date_str),
        )
    return _make


@pytest.fixture
def make_masterplan():
    """Factory for mock Masterplan objects."""
    def _make(zoning_type="mixed", fsi=2.5, ground_coverage_pct=60, max_height_m=45):
        return SimpleNamespace(
            zoning_type=zoning_type,
            fsi=Decimal(str(fsi)),
            ground_coverage_pct=Decimal(str(ground_coverage_pct)),
            max_height_m=Decimal(str(max_height_m)),
        )
    return _make


@pytest.fixture
def make_census():
    """Factory for mock CensusData objects."""
    def _make(density_per_sqkm=10000, growth_rate_pct=5.0, population=150000, households=35000):
        return SimpleNamespace(
            density_per_sqkm=Decimal(str(density_per_sqkm)),
            growth_rate_pct=Decimal(str(growth_rate_pct)),
            population=population,
            households=households,
            year=2024,
        )
    return _make
