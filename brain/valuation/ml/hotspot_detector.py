"""Hotspot detection using KMeans clustering on location features."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from brain.data_bank.models import Location, PropertyPrice
from brain.valuation.models import ValuationScore

logger = logging.getLogger(__name__)


@dataclass
class HotspotFeature:
    key: str
    label: str
    average: float
    delta_from_baseline: float
    relative_level: str


@dataclass
class Hotspot:
    cluster_id: int
    label: str  # "high_growth", "undervalued", "premium", "emerging"
    summary: str
    cluster_size: int
    hotspot_score: float
    dominant_signal: str
    locations: list[dict]  # [{location_id, name, scores...}]
    avg_land_value: float
    avg_development_potential: float
    avg_appreciation: float
    avg_infra_score: float
    avg_price_trend: float
    avg_price: float
    feature_profile: list[HotspotFeature] = field(default_factory=list)


class HotspotDetector:
    """Detect investment hotspots by clustering locations on valuation features.

    Uses KMeans to group locations into clusters, then labels each cluster
    based on its aggregate characteristics.
    """

    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self._centroids: np.ndarray | None = None
        self._labels: list[str] = []

    FEATURE_META = (
        ("land_value_score", "Land Value Score"),
        ("development_potential_score", "Development Potential Score"),
        ("future_appreciation_index", "Future Appreciation Index"),
        ("infra_score", "Infra Score"),
        ("price_trend_score", "Price Trend Score"),
        ("density_score", "Density Score"),
        ("avg_price", "Avg Price / sqft"),
    )

    def _normalize_scalar(self, value: float, min_value: float, max_value: float) -> float:
        if max_value == min_value:
            return 50.0
        return max(0.0, min(100.0, ((value - min_value) / (max_value - min_value)) * 100))

    def _cluster_metrics(self, members: list[dict]) -> dict:
        def values(key: str, default: float) -> list[float]:
            return [float(m.get(key, default)) for m in members]

        return {
            "land_value_score": float(np.mean(values("land_value_score", 50.0))),
            "development_potential_score": float(np.mean(values("development_potential_score", 50.0))),
            "future_appreciation_index": float(np.mean(values("future_appreciation_index", 50.0))),
            "infra_score": float(np.mean(values("infra_score", 60.0))),
            "price_trend_score": float(np.mean(values("price_trend_score", 55.0))),
            "density_score": float(np.mean(values("density_score", 50.0))),
            "avg_price": float(np.mean(values("avg_price", 9000.0))),
        }

    def _feature_baseline(self, meta: list[dict]) -> dict:
        baseline: dict[str, dict[str, float]] = {}
        if not meta:
            for key, _label in self.FEATURE_META:
                baseline[key] = {"mean": 0.0, "std": 1.0, "min": 0.0, "max": 100.0}
            return baseline

        for key, _label in self.FEATURE_META:
            values = np.array([float(item[key]) for item in meta], dtype=float)
            std = float(values.std()) if values.size else 1.0
            baseline[key] = {
                "mean": float(values.mean()) if values.size else 0.0,
                "std": std if std > 0 else 1.0,
                "min": float(values.min()) if values.size else 0.0,
                "max": float(values.max()) if values.size else 100.0,
            }
        return baseline

    def _build_feature_profile(self, members: list[dict], baseline: dict) -> list[HotspotFeature]:
        if not members:
            return []

        metrics = self._cluster_metrics(members)
        profile: list[HotspotFeature] = []
        for key, label in self.FEATURE_META:
            mean = baseline[key]["mean"]
            std = baseline[key]["std"]
            average = metrics[key]
            delta = average - mean
            normalized_delta = delta / std if std else 0.0

            if normalized_delta >= 0.5:
                relative_level = "high"
            elif normalized_delta <= -0.5:
                relative_level = "low"
            else:
                relative_level = "neutral"

            profile.append(
                HotspotFeature(
                    key=key,
                    label=label,
                    average=round(average, 2),
                    delta_from_baseline=round(delta, 2),
                    relative_level=relative_level,
                )
            )

        profile.sort(key=lambda item: abs(item.delta_from_baseline), reverse=True)
        return profile[:3]

    def _hotspot_score(self, members: list[dict], baseline: dict) -> float:
        metrics = self._cluster_metrics(members)
        price_advantage = 100 - self._normalize_scalar(
            metrics["avg_price"],
            baseline["avg_price"]["min"],
            baseline["avg_price"]["max"],
        )
        score = (
            (metrics["future_appreciation_index"] * 0.30)
            + (metrics["development_potential_score"] * 0.24)
            + (metrics["land_value_score"] * 0.18)
            + (metrics["infra_score"] * 0.14)
            + (metrics["price_trend_score"] * 0.08)
            + (price_advantage * 0.06)
        )
        return round(min(100.0, max(0.0, score)), 2)

    def _dominant_signal(self, label: str, feature_profile: list[HotspotFeature]) -> str:
        if label == "undervalued":
            return "value_gap"
        if label == "premium":
            return "premium_core"
        if label == "emerging":
            return "buildout_corridor"
        if label == "high_growth":
            return "growth_momentum"
        if feature_profile:
            return feature_profile[0].key
        return "balanced"

    def _build_summary(self, label: str, cluster_size: int, feature_profile: list[HotspotFeature]) -> str:
        if not feature_profile:
            return f"{label.replace('_', ' ').title()} cluster across {cluster_size} locations."

        lead = feature_profile[0]
        lead_text = f"{lead.label.lower()} is {lead.relative_level} versus the market baseline"
        if len(feature_profile) > 1:
            secondary = feature_profile[1]
            secondary_text = f"{secondary.label.lower()} is {secondary.relative_level}"
            return (
                f"{label.replace('_', ' ').title()} cluster across {cluster_size} locations where "
                f"{lead_text} and {secondary_text}."
            )
        return f"{label.replace('_', ' ').title()} cluster across {cluster_size} locations where {lead_text}."

    def _extract_features(self, session: Session) -> tuple[np.ndarray, list[dict]]:
        """Build feature matrix from valuation scores.

        Features per location:
        0. land_value_score
        1. development_potential_score
        2. future_appreciation_index
        3. infra_score
        4. price_trend_score
        5. density_score
        6. avg_price_per_sqft (normalized)
        """
        # Get latest scores per location
        subq = (
            select(
                ValuationScore.location_id,
                func.max(ValuationScore.id).label("max_id"),
            )
            .group_by(ValuationScore.location_id)
            .subquery()
        )

        q = (
            select(ValuationScore, Location.name)
            .join(subq, ValuationScore.id == subq.c.max_id)
            .join(Location, ValuationScore.location_id == Location.id)
        )

        rows = []
        meta = []
        for vs, name in session.execute(q):
            # Get avg price
            avg_price = session.scalar(
                select(func.avg(PropertyPrice.price_per_sqft))
                .where(PropertyPrice.location_id == vs.location_id)
            )
            avg_price = float(avg_price) if avg_price else 5000

            rows.append([
                float(vs.land_value_score or 0),
                float(vs.development_potential_score or 0),
                float(vs.future_appreciation_index or 0),
                float(vs.infra_score or 0),
                float(vs.price_trend_score or 0),
                float(vs.density_score or 0),
                avg_price / 100,  # scale down to similar range as scores
            ])
            meta.append({
                "location_id": vs.location_id,
                "name": name,
                "land_value_score": float(vs.land_value_score or 0),
                "development_potential_score": float(vs.development_potential_score or 0),
                "future_appreciation_index": float(vs.future_appreciation_index or 0),
                "infra_score": float(vs.infra_score or 0),
                "price_trend_score": float(vs.price_trend_score or 0),
                "density_score": float(vs.density_score or 0),
                "avg_price": avg_price,
            })

        return np.array(rows) if rows else np.array([]).reshape(0, 7), meta

    def _initialize_centroids(self, X: np.ndarray, k: int) -> np.ndarray:
        rng = np.random.default_rng(42)
        first_index = int(rng.integers(0, X.shape[0]))
        centroids = [X[first_index].copy()]

        while len(centroids) < k:
            centroid_array = np.array(centroids)
            distances = np.min(
                np.linalg.norm(X[:, np.newaxis] - centroid_array[np.newaxis, :], axis=2) ** 2,
                axis=1,
            )
            total_distance = float(distances.sum())
            if total_distance <= 0:
                remaining = [idx for idx in range(X.shape[0]) if not any(np.array_equal(X[idx], existing) for existing in centroids)]
                if not remaining:
                    break
                next_index = int(rng.choice(remaining))
            else:
                probabilities = distances / total_distance
                next_index = int(rng.choice(X.shape[0], p=probabilities))
            centroids.append(X[next_index].copy())

        return np.array(centroids)

    def _kmeans(self, X: np.ndarray, max_iters: int = 100) -> tuple[np.ndarray, np.ndarray]:
        """Simple KMeans implementation (no sklearn dependency)."""
        n_samples = X.shape[0]
        if n_samples == 0:
            return np.array([], dtype=int), np.array([])
        k = min(self.n_clusters, n_samples)

        # Initialize centroids with k-means++ style seeding for more stable clustering.
        centroids = self._initialize_centroids(X, k)

        labels = np.zeros(n_samples, dtype=int)

        for _ in range(max_iters):
            # Assign clusters
            distances = np.linalg.norm(X[:, np.newaxis] - centroids[np.newaxis, :], axis=2)
            new_labels = distances.argmin(axis=1)

            if np.array_equal(labels, new_labels):
                break
            labels = new_labels

            # Update centroids
            for i in range(k):
                mask = labels == i
                if mask.any():
                    centroids[i] = X[mask].mean(axis=0)

        return labels, centroids

    def _label_cluster(self, members: list[dict], baseline: dict | None = None) -> str:
        """Label a cluster based on aggregate characteristics."""
        if not members:
            return "unknown"

        metrics = self._cluster_metrics(members)
        avg_appreciation = metrics["future_appreciation_index"]
        avg_land_value = metrics["land_value_score"]
        avg_price = metrics["avg_price"]
        avg_dev = metrics["development_potential_score"]
        avg_infra = metrics["infra_score"]
        avg_trend = metrics["price_trend_score"]
        baseline_price = baseline["avg_price"]["mean"] if baseline else 9000.0

        # High appreciation + low price = undervalued gem
        if avg_appreciation >= 65 and avg_price <= (baseline_price * 0.92):
            return "undervalued"
        # High everything = premium
        if avg_land_value >= 72 and avg_price >= (baseline_price * 1.10):
            return "premium"
        # High dev potential + strong infra + appreciation = emerging corridor
        if avg_dev >= 65 and avg_infra >= 60 and avg_appreciation >= 58:
            return "emerging"
        # High appreciation and price momentum = high growth
        if avg_appreciation >= 60 and avg_trend >= 58:
            return "high_growth"
        if avg_appreciation < 48 and avg_dev < 50:
            return "watchlist"

        return "stable"

    def detect(self, session: Session) -> list[Hotspot]:
        """Run hotspot detection. Returns clusters with labels."""
        X, meta = self._extract_features(session)
        baseline = self._feature_baseline(meta)

        if len(X) < 2:
            logger.warning("Not enough scored locations for clustering (need >= 2)")
            return []

        # Normalize features
        means = X.mean(axis=0)
        stds = X.std(axis=0)
        stds[stds == 0] = 1.0
        X_norm = (X - means) / stds

        labels, centroids = self._kmeans(X_norm)
        self._centroids = centroids

        # Group by cluster
        clusters: dict[int, list[dict]] = {}
        for i, label in enumerate(labels):
            clusters.setdefault(int(label), []).append(meta[i])

        hotspots = []
        for cluster_id, members in sorted(clusters.items()):
            metrics = self._cluster_metrics(members)
            label = self._label_cluster(members, baseline)
            feature_profile = self._build_feature_profile(members, baseline)
            hotspot_score = self._hotspot_score(members, baseline)
            dominant_signal = self._dominant_signal(label, feature_profile)
            hotspots.append(Hotspot(
                cluster_id=cluster_id,
                label=label,
                summary=self._build_summary(label, len(members), feature_profile),
                cluster_size=len(members),
                hotspot_score=hotspot_score,
                dominant_signal=dominant_signal,
                locations=members,
                avg_land_value=round(metrics["land_value_score"], 2),
                avg_development_potential=round(metrics["development_potential_score"], 2),
                avg_appreciation=round(metrics["future_appreciation_index"], 2),
                avg_infra_score=round(metrics["infra_score"], 2),
                avg_price_trend=round(metrics["price_trend_score"], 2),
                avg_price=round(metrics["avg_price"], 2),
                feature_profile=feature_profile,
            ))

        hotspots.sort(key=lambda hotspot: (-hotspot.hotspot_score, hotspot.label, hotspot.cluster_id))
        logger.info("Detected %d hotspot clusters", len(hotspots))
        return hotspots
