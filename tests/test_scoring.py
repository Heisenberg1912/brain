"""Tests for brain.valuation.scoring — the core scoring engine."""
from datetime import date
from types import SimpleNamespace

import pytest

from brain.valuation.scoring import (
    _normalize,
    compute_climate_exposure_score,
    compute_climate_resilience_score,
    compute_demand_pressure_score,
    compute_infra_proximity_profile,
    compute_market_momentum_score,
    compute_mobility_score,
    compute_infra_score,
    compute_masterplan_zoning_shift_score,
    compute_overall_favorability_score,
    compute_population_growth_score,
    compute_price_trend,
    compute_regulatory_clarity_score,
    compute_site_readiness_score,
    compute_site_risk_score,
    compute_terrain_constraint_score,
    compute_terrain_readiness_score,
    compute_use_case_favorability,
    compute_zoning_favorability,
    compute_density_score,
    compute_land_value_score,
    compute_development_potential,
    compute_future_appreciation,
    ZONE_VALUE,
)


# ── _normalize ─────────────────────────────────────────────

class TestNormalize:
    def test_midpoint(self):
        assert _normalize(50, 0, 100) == 50.0

    def test_min_value(self):
        assert _normalize(0, 0, 100) == 0.0

    def test_max_value(self):
        assert _normalize(100, 0, 100) == 100.0

    def test_below_min_clamps_to_zero(self):
        assert _normalize(-10, 0, 100) == 0.0

    def test_above_max_clamps_to_100(self):
        assert _normalize(200, 0, 100) == 100.0

    def test_equal_min_max_returns_50(self):
        assert _normalize(5, 5, 5) == 50.0


# ── compute_infra_score ────────────────────────────────────

class TestInfraScore:
    def test_no_infra_returns_baseline(self):
        assert compute_infra_score([]) == 10.0

    def test_close_metro_scores_high(self, make_infra):
        infra = [make_infra("metro_station", "operational", 0.5)]
        score = compute_infra_score(infra)
        # metro weight=25, proximity=0.9, operational=1.0 → 22.5
        assert score == pytest.approx(22.5, abs=0.1)

    def test_far_infra_scores_low(self, make_infra):
        infra = [make_infra("school", "operational", 4.5)]
        score = compute_infra_score(infra)
        # school weight=10, proximity=0.1 → 1.0
        assert score == pytest.approx(1.0, abs=0.1)

    def test_at_5km_boundary_no_contribution(self, make_infra):
        infra = [make_infra("metro_station", "operational", 5.0)]
        score = compute_infra_score(infra)
        assert score == 0.0

    def test_planned_infra_gets_bonus(self, make_infra):
        operational = [make_infra("metro_station", "operational", 1.0)]
        planned = [make_infra("metro_station", "planned", 1.0)]
        assert compute_infra_score(planned) > compute_infra_score(operational)

    def test_multiple_infra_accumulates(self, make_infra):
        single = [make_infra("metro_station", "operational", 1.0)]
        multiple = [
            make_infra("metro_station", "operational", 1.0),
            make_infra("hospital", "operational", 2.0),
            make_infra("school", "operational", 1.5),
        ]
        assert compute_infra_score(multiple) > compute_infra_score(single)

    def test_score_capped_at_100(self, make_infra):
        # Many close items
        infra = [make_infra("metro_station", "planned", 0.1) for _ in range(20)]
        assert compute_infra_score(infra) == 100.0

    def test_infra_proximity_profile_highlights_strategic_access(self, make_infra):
        profile = type("Geo", (), {"road_proximity_km": 0.8, "transit_proximity_km": 0.7})()
        nearby = [
            make_infra("metro_station", "operational", 0.6),
            make_infra("tech_park", "operational", 1.2),
            make_infra("highway", "operational", 1.4),
        ]

        result = compute_infra_proximity_profile(nearby, profile)

        assert result["road_access_score"] > 85
        assert result["metro_access_score"] > 85
        assert result["economic_access_score"] > 85
        assert result["strategic_infra_score"] > 85

    def test_infra_proximity_profile_stays_bounded_when_missing(self):
        result = compute_infra_proximity_profile([], None)

        assert 0 <= result["strategic_infra_score"] <= 100
        assert result["metro_proximity_km"] is None


# ── compute_price_trend ────────────────────────────────────

class TestPriceTrend:
    def test_single_price_returns_neutral(self, make_price):
        prices = [make_price(5000, "2024-01-01")]
        assert compute_price_trend(prices) == 50.0

    def test_no_prices_returns_neutral(self):
        assert compute_price_trend([]) == 50.0

    def test_positive_growth(self, make_price):
        prices = [
            make_price(5000, "2023-01-01"),
            make_price(6000, "2024-01-01"),
        ]
        score = compute_price_trend(prices)
        # 20% growth → 50 + (20 * 2.5) = 100
        assert score == 100.0

    def test_negative_growth(self, make_price):
        prices = [
            make_price(6000, "2023-01-01"),
            make_price(5400, "2024-01-01"),
        ]
        score = compute_price_trend(prices)
        # -10% → 50 + (-10 * 2.5) = 25
        assert score == pytest.approx(25.0, abs=0.1)

    def test_flat_prices(self, make_price):
        prices = [
            make_price(5000, "2023-01-01"),
            make_price(5000, "2024-01-01"),
        ]
        assert compute_price_trend(prices) == 50.0

    def test_zero_oldest_returns_neutral(self, make_price):
        prices = [
            make_price(0, "2023-01-01"),
            make_price(5000, "2024-01-01"),
        ]
        assert compute_price_trend(prices) == 50.0

    def test_score_clamps_to_bounds(self, make_price):
        # Extreme drop
        prices = [make_price(10000, "2023-01-01"), make_price(1000, "2024-01-01")]
        assert compute_price_trend(prices) >= 0
        assert compute_price_trend(prices) <= 100


# ── compute_zoning_favorability ────────────────────────────

class TestZoningFavorability:
    def test_no_masterplan(self):
        assert compute_zoning_favorability(None) == 30.0

    def test_mixed_high_fsi(self, make_masterplan):
        mp = make_masterplan("mixed", fsi=3.0)
        score = compute_zoning_favorability(mp)
        # (90 * 0.5) + (min(100, 90) * 0.5) = 45 + 45 = 90
        assert score == pytest.approx(90.0, abs=0.1)

    def test_industrial_low_fsi(self, make_masterplan):
        mp = make_masterplan("industrial", fsi=1.0)
        score = compute_zoning_favorability(mp)
        # (50 * 0.5) + (30 * 0.5) = 25 + 15 = 40
        assert score == pytest.approx(40.0, abs=0.1)

    def test_commercial_mid_fsi(self, make_masterplan):
        mp = make_masterplan("commercial", fsi=2.0)
        score = compute_zoning_favorability(mp)
        # (85 * 0.5) + (60 * 0.5) = 42.5 + 30 = 72.5
        assert score == pytest.approx(72.5, abs=0.1)

    def test_unknown_zone_type(self, make_masterplan):
        mp = make_masterplan("special_economic", fsi=2.0)
        score = compute_zoning_favorability(mp)
        # (50 * 0.5) + (60 * 0.5) = 25 + 30 = 55
        assert score == pytest.approx(55.0, abs=0.1)


# ── compute_density_score ──────────────────────────────────

class TestDensityScore:
    def test_no_census(self):
        assert compute_density_score(None) == 50.0

    def test_sweet_spot_density(self, make_census):
        census = make_census(density_per_sqkm=12000)
        score = compute_density_score(census)
        assert 60 <= score <= 90

    def test_low_density_penalized(self, make_census):
        census = make_census(density_per_sqkm=2000)
        score = compute_density_score(census)
        assert score < 50

    def test_very_high_density_penalized(self, make_census):
        census = make_census(density_per_sqkm=22000)
        score = compute_density_score(census)
        # Should be penalized but floor at 40
        assert 40 <= score <= 70

    def test_zero_density(self, make_census):
        census = make_census(density_per_sqkm=0)
        score = compute_density_score(census)
        assert score == 0.0

    def test_none_density(self, make_census):
        census = make_census(density_per_sqkm=0)
        census.density_per_sqkm = None
        score = compute_density_score(census)
        assert score == 0.0


class TestDemandSignals:
    def test_population_growth_score_rewards_fast_growth(self):
        fast = compute_population_growth_score(7.0)
        slow = compute_population_growth_score(1.0)

        assert fast > slow

    def test_demand_pressure_blends_growth_and_density(self):
        strong = compute_demand_pressure_score(6.0, 80.0)
        weak = compute_demand_pressure_score(1.0, 35.0)

        assert strong > weak
        assert 0 <= strong <= 100


class TestGeoScores:
    def test_missing_geo_profile_returns_neutral(self):
        assert compute_climate_resilience_score(None) == 50.0
        assert compute_terrain_readiness_score(None) == 50.0
        assert compute_climate_exposure_score(None) == 50.0
        assert compute_terrain_constraint_score(None) == 50.0
        assert compute_site_risk_score(None) == 50.0

    def test_low_risk_profile_scores_high(self):
        profile = type("Geo", (), {
            "flood_risk_score": 20,
            "heat_risk_score": 25,
            "climate_risk_score": 22,
            "terrain_class": "flat",
            "terrain_slope_pct": 2,
        })()
        assert compute_climate_resilience_score(profile) > 70
        assert compute_terrain_readiness_score(profile) > 75
        assert compute_climate_exposure_score(profile) < 30
        assert compute_terrain_constraint_score(profile) < 25
        assert compute_site_risk_score(profile) < 30

    def test_high_risk_steep_profile_scores_lower(self):
        profile = type("Geo", (), {
            "flood_risk_score": 80,
            "heat_risk_score": 75,
            "climate_risk_score": 85,
            "terrain_class": "steep",
            "terrain_slope_pct": 18,
        })()
        assert compute_climate_resilience_score(profile) < 35
        assert compute_terrain_readiness_score(profile) < 55
        assert compute_climate_exposure_score(profile) > 65
        assert compute_terrain_constraint_score(profile) > 45
        assert compute_site_risk_score(profile) > 55


# ── compute_land_value_score ───────────────────────────────

class TestLandValueScore:
    def test_all_high_inputs(self, sample_weights):
        score = compute_land_value_score(
            avg_price=12000, infra_score=90, zoning_favorability=85,
            density_score=80, price_trend=75, weights=sample_weights,
        )
        assert 70 <= score <= 100

    def test_all_low_inputs(self, sample_weights):
        score = compute_land_value_score(
            avg_price=3000, infra_score=10, zoning_favorability=30,
            density_score=20, price_trend=25, weights=sample_weights,
        )
        assert score < 30

    def test_none_price_uses_default(self, sample_weights):
        score = compute_land_value_score(
            avg_price=None, infra_score=50, zoning_favorability=50,
            density_score=50, price_trend=50, weights=sample_weights,
        )
        assert 0 <= score <= 100

    def test_score_within_bounds(self, sample_weights):
        score = compute_land_value_score(
            avg_price=8000, infra_score=50, zoning_favorability=50,
            density_score=50, price_trend=50, weights=sample_weights,
        )
        assert 0 <= score <= 100


# ── compute_development_potential ──────────────────────────

class TestDevelopmentPotential:
    def test_high_fsi_high_planned_infra(self, make_masterplan, sample_weights):
        mp = make_masterplan("mixed", fsi=3.5)
        score = compute_development_potential(mp, infra_planned_count=4, price_growth_rate=75, weights=sample_weights)
        assert score > 60

    def test_no_masterplan(self, sample_weights):
        score = compute_development_potential(None, infra_planned_count=0, price_growth_rate=50, weights=sample_weights)
        assert 0 <= score <= 100

    def test_zero_planned_infra(self, make_masterplan, sample_weights):
        mp = make_masterplan("residential", fsi=1.5)
        score = compute_development_potential(mp, infra_planned_count=0, price_growth_rate=50, weights=sample_weights)
        assert 0 <= score <= 100

    def test_infra_count_caps_at_4(self, make_masterplan, sample_weights):
        mp = make_masterplan("mixed", fsi=2.0)
        score_4 = compute_development_potential(mp, infra_planned_count=4, price_growth_rate=50, weights=sample_weights)
        score_10 = compute_development_potential(mp, infra_planned_count=10, price_growth_rate=50, weights=sample_weights)
        assert score_4 == score_10  # both cap at 100 for infra_planned


# ── compute_future_appreciation ────────────────────────────

class TestFutureAppreciation:
    def test_high_growth_area(self, sample_weights):
        score = compute_future_appreciation(
            price_trend=80, infra_pipeline_count=3,
            population_growth_pct=8.0, zoning_type="industrial",
            weights=sample_weights,
        )
        assert score > 60

    def test_stagnant_area(self, sample_weights):
        score = compute_future_appreciation(
            price_trend=30, infra_pipeline_count=0,
            population_growth_pct=1.0, zoning_type="commercial",
            weights=sample_weights,
        )
        assert score < 40

    def test_none_zoning(self, sample_weights):
        score = compute_future_appreciation(
            price_trend=50, infra_pipeline_count=1,
            population_growth_pct=5.0, zoning_type=None,
            weights=sample_weights,
        )
        assert 0 <= score <= 100

    def test_masterplan_upzoning_improves_future_appreciation(self, sample_weights):
        uplifted = compute_future_appreciation(
            price_trend=50,
            infra_pipeline_count=1,
            population_growth_pct=5.0,
            zoning_type="mixed",
            weights=sample_weights,
            zoning_shift_score=92,
        )
        constrained = compute_future_appreciation(
            price_trend=50,
            infra_pipeline_count=1,
            population_growth_pct=5.0,
            zoning_type="mixed",
            weights=sample_weights,
            zoning_shift_score=42,
        )

        assert uplifted > constrained

    def test_demand_pressure_improves_future_appreciation(self, sample_weights):
        strong = compute_future_appreciation(
            price_trend=50,
            infra_pipeline_count=1,
            population_growth_pct=4.0,
            zoning_type="mixed",
            weights=sample_weights,
            demand_pressure_score=78,
        )
        weak = compute_future_appreciation(
            price_trend=50,
            infra_pipeline_count=1,
            population_growth_pct=4.0,
            zoning_type="mixed",
            weights=sample_weights,
            demand_pressure_score=32,
        )

        assert strong > weak

    def test_all_scores_bounded(self, sample_weights):
        """All outputs should be in 0-100 range regardless of inputs."""
        for trend in [0, 50, 100]:
            for infra in [0, 2, 5]:
                for pop in [0, 5, 10]:
                    for zone in ["residential", "mixed", "industrial", "commercial", None]:
                        score = compute_future_appreciation(trend, infra, pop, zone, sample_weights)
                        assert 0 <= score <= 100, f"Out of bounds: {score} for inputs ({trend}, {infra}, {pop}, {zone})"


class TestFavorabilityHelpers:
    def test_masterplan_zoning_shift_score_rewards_upzoning(self):
        history = [
            SimpleNamespace(zoning_type="residential", effective_from=date(2020, 1, 1), created_at=None, id=1),
            SimpleNamespace(zoning_type="mixed", effective_from=date(2025, 1, 1), created_at=None, id=2),
        ]

        score = compute_masterplan_zoning_shift_score(history, zoning_type="mixed")

        assert score > 90

    def test_masterplan_zoning_shift_score_penalizes_downzoning(self):
        history = [
            SimpleNamespace(zoning_type="mixed", effective_from=date(2020, 1, 1), created_at=None, id=1),
            SimpleNamespace(zoning_type="residential", effective_from=date(2025, 1, 1), created_at=None, id=2),
        ]

        score = compute_masterplan_zoning_shift_score(history, zoning_type="residential")

        assert score < 45

    def test_regulatory_clarity_improves_with_context_and_standards(self):
        masterplan = type("Masterplan", (), {"approval_status": "active"})()
        planning_context = type("Planning", (), {
            "validation_status": "derived",
            "zoning_validation_rules": {"coverage": True},
            "floor_plan_constraints": {"fsi": 2.5},
        })()
        standards = [object(), object()]

        score = compute_regulatory_clarity_score(masterplan, planning_context, standards)

        assert score > 70

    def test_mobility_score_rewards_close_transit(self, make_infra):
        nearby = [make_infra("metro_station", "operational", 0.5)]
        profile = type("Geo", (), {"road_proximity_km": 1.0, "transit_proximity_km": 0.4})()

        score = compute_mobility_score(nearby, profile)

        assert score > 60

    def test_residential_use_case_prefers_residential_zoning(self):
        residential = compute_use_case_favorability(
            "residential",
            zoning_type="residential",
            land_value_score=65,
            development_potential_score=68,
            future_appreciation_index=62,
            infra_score=60,
            density_score=72,
            climate_resilience_score=74,
            terrain_readiness_score=80,
        )
        industrial = compute_use_case_favorability(
            "residential",
            zoning_type="industrial",
            land_value_score=65,
            development_potential_score=68,
            future_appreciation_index=62,
            infra_score=60,
            density_score=72,
            climate_resilience_score=74,
            terrain_readiness_score=80,
        )

        assert residential > industrial

    def test_overall_favorability_stays_bounded(self):
        market = compute_market_momentum_score(80, 75, 70)
        site = compute_site_readiness_score(
            type("Masterplan", (), {"fsi": 3.0, "max_height_m": 48, "ground_coverage_pct": 62})(),
            type("Geo", (), {
                "flood_risk_score": 20,
                "heat_risk_score": 25,
                "climate_risk_score": 22,
                "terrain_class": "flat",
                "terrain_slope_pct": 2,
            })(),
        )
        overall = compute_overall_favorability_score(
            market_momentum_score=market,
            site_readiness_score=site,
            regulatory_clarity_score=72,
            mobility_score=68,
            best_use_case_score=78,
        )

        assert 0 <= overall <= 100
