"""Tests for ML models — price predictor and hotspot detector (unit tests, no DB)."""
import pytest
import numpy as np

from brain.valuation.ml.price_predictor import PricePredictor, PricePrediction
from brain.valuation.ml.hotspot_detector import HotspotDetector


class TestPricePredictor:
    def test_initial_state(self):
        p = PricePredictor()
        assert p._trained is False
        assert p._weights is None

    def test_normalize_features(self):
        p = PricePredictor()
        X = np.array([[10, 20], [30, 40], [50, 60]], dtype=float)
        X_norm = p._normalize_features(X, fit=True)
        # After normalization, mean should be ~0 and std ~1
        assert np.abs(X_norm.mean(axis=0)).max() < 1e-10
        assert np.abs(X_norm.std(axis=0) - 1.0).max() < 1e-10

    def test_normalize_handles_zero_std(self):
        p = PricePredictor()
        # Column with constant value (std=0)
        X = np.array([[5, 10], [5, 20], [5, 30]], dtype=float)
        X_norm = p._normalize_features(X, fit=True)
        # Should not produce NaN or inf
        assert not np.isnan(X_norm).any()
        assert not np.isinf(X_norm).any()

    def test_prediction_dataclass(self):
        pred = PricePrediction(
            location_id=1,
            location_name="Whitefield",
            current_avg_price=8000,
            predicted_price_1yr=8800,
            predicted_price_3yr=10648,
            annual_growth_pct=10.0,
            confidence="medium",
        )
        assert pred.location_name == "Whitefield"
        assert pred.annual_growth_pct == 10.0
        assert pred.signal == "neutral"
        assert pred.training_locations == 0

    def test_annualized_growth_pct_handles_one_year_gain(self):
        p = PricePredictor()
        annualized = p._annualized_growth_pct(100.0, 110.0, 365)
        assert annualized == pytest.approx(10.0, abs=0.02)

    def test_signal_from_upside_uses_simple_bands(self):
        p = PricePredictor()
        assert p._signal_from_upside(15.0) == "bullish"
        assert p._signal_from_upside(7.0) == "positive"
        assert p._signal_from_upside(1.0) == "neutral"
        assert p._signal_from_upside(-2.0) == "cautious"

    def test_fallback_growth_rate_returns_drivers(self):
        p = PricePredictor()
        predicted_growth, drivers = p._fallback_growth_rate(
            {
                "annualized_growth_pct": 8.0,
                "historical_growth_pct": 12.0,
                "population_growth_pct": 4.0,
                "fsi": 2.5,
            },
            np.array([11200.0, 12.0, 11800.0, 4.0, 2.5, 78.0, 82.0, 76.0], dtype=float),
        )
        assert predicted_growth > 0
        assert len(drivers) == 3
        assert drivers[0].key == "historical_growth_pct"


class TestHotspotDetector:
    def test_kmeans_basic(self):
        detector = HotspotDetector(n_clusters=2)
        # Two clearly separated clusters
        X = np.array([
            [0, 0], [1, 0], [0, 1],  # cluster near origin
            [10, 10], [11, 10], [10, 11],  # cluster far away
        ], dtype=float)
        labels, centroids = detector._kmeans(X)
        assert len(set(labels)) == 2
        assert centroids.shape == (2, 2)
        # Points in same group should have same label
        assert labels[0] == labels[1] == labels[2]
        assert labels[3] == labels[4] == labels[5]
        assert labels[0] != labels[3]

    def test_kmeans_single_cluster(self):
        detector = HotspotDetector(n_clusters=1)
        X = np.array([[1, 2], [3, 4], [5, 6]], dtype=float)
        labels, centroids = detector._kmeans(X)
        assert set(labels) == {0}

    def test_label_cluster_undervalued(self):
        detector = HotspotDetector()
        members = [
            {"future_appreciation_index": 75, "land_value_score": 50, "avg_price": 5000, "development_potential_score": 60},
        ]
        assert detector._label_cluster(members) == "undervalued"

    def test_label_cluster_premium(self):
        detector = HotspotDetector()
        members = [
            {"future_appreciation_index": 70, "land_value_score": 80, "avg_price": 12000, "development_potential_score": 70},
        ]
        assert detector._label_cluster(members) == "premium"

    def test_label_cluster_emerging(self):
        detector = HotspotDetector()
        members = [
            {"future_appreciation_index": 60, "land_value_score": 50, "avg_price": 9000, "development_potential_score": 65},
        ]
        assert detector._label_cluster(members) == "emerging"

    def test_label_cluster_empty(self):
        detector = HotspotDetector()
        assert detector._label_cluster([]) == "unknown"

    def test_n_clusters_capped_by_samples(self):
        detector = HotspotDetector(n_clusters=10)
        X = np.array([[1, 2], [3, 4], [5, 6]], dtype=float)
        labels, centroids = detector._kmeans(X)
        # Should cap at 3 clusters (n_samples)
        assert centroids.shape[0] == 3

    def test_build_feature_profile_surfaces_dominant_deltas(self):
        detector = HotspotDetector()
        members = [
            {
                "land_value_score": 82.0,
                "development_potential_score": 86.0,
                "future_appreciation_index": 78.0,
                "infra_score": 74.0,
                "price_trend_score": 69.0,
                "density_score": 66.0,
                "avg_price": 8900.0,
            },
            {
                "land_value_score": 80.0,
                "development_potential_score": 84.0,
                "future_appreciation_index": 76.0,
                "infra_score": 72.0,
                "price_trend_score": 70.0,
                "density_score": 64.0,
                "avg_price": 9100.0,
            },
        ]
        baseline = detector._feature_baseline(
            members
            + [
                {
                    "land_value_score": 55.0,
                    "development_potential_score": 58.0,
                    "future_appreciation_index": 54.0,
                    "infra_score": 48.0,
                    "price_trend_score": 50.0,
                    "density_score": 52.0,
                    "avg_price": 12000.0,
                }
            ]
        )

        profile = detector._build_feature_profile(members, baseline)

        assert len(profile) == 3
        assert profile[0].relative_level in {"high", "low"}
        assert any(item.key == "avg_price" for item in profile)

    def test_hotspot_score_rewards_upside_and_value_gap(self):
        detector = HotspotDetector()
        premium_like = [
            {
                "land_value_score": 82.0,
                "development_potential_score": 76.0,
                "future_appreciation_index": 66.0,
                "infra_score": 70.0,
                "price_trend_score": 62.0,
                "density_score": 64.0,
                "avg_price": 12500.0,
            }
        ]
        value_like = [
            {
                "land_value_score": 72.0,
                "development_potential_score": 78.0,
                "future_appreciation_index": 81.0,
                "infra_score": 72.0,
                "price_trend_score": 68.0,
                "density_score": 61.0,
                "avg_price": 8500.0,
            }
        ]
        baseline = detector._feature_baseline(premium_like + value_like)

        premium_score = detector._hotspot_score(premium_like, baseline)
        value_score = detector._hotspot_score(value_like, baseline)

        assert value_score > premium_score
