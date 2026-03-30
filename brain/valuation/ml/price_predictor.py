"""Direct regression model for 1Y property price prediction."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.data_bank.models import Location, PropertyPrice, CensusData, Masterplan
from brain.valuation.models import ValuationScore

logger = logging.getLogger(__name__)


@dataclass
class PredictionDriver:
    key: str
    label: str
    value: float
    contribution: float
    direction: str


@dataclass
class PricePrediction:
    location_id: int
    location_name: str
    current_avg_price: float
    predicted_price_1yr: float
    predicted_price_3yr: float
    annual_growth_pct: float
    confidence: str  # "low", "medium", "high"
    predicted_upside_pct: float = 0.0
    signal: str = "neutral"
    model_version: str = "growth_regression_v1"
    training_locations: int = 0
    r_squared: float | None = None
    drivers: list[PredictionDriver] = field(default_factory=list)
    summary: str = ""


class PricePredictor:
    """Predicts future property prices using a direct linear regression model.

    Features: current price, trailing momentum, density, population growth,
    FSI, and latest valuation scores.
    Target: 1-year forward annualized price per sqft.
    """

    MODEL_VERSION = "price_regression_v2"
    FALLBACK_MODEL_VERSION = "price_regression_fallback_v1"
    TARGET_HORIZON_DAYS = 365.25
    FEATURE_KEYS = (
        "current_price_per_sqft",
        "trailing_growth_pct",
        "density_per_sqkm",
        "population_growth_pct",
        "fsi",
        "land_value_score",
        "development_potential_score",
        "future_appreciation_index",
    )
    FEATURE_LABELS = {
        "current_price_per_sqft": "Current Price / sqft",
        "trailing_growth_pct": "Trailing Annualized Growth %",
        "historical_growth_pct": "Historical Growth %",
        "density_per_sqkm": "Density / sqkm",
        "population_growth_pct": "Population Growth %",
        "fsi": "FSI",
        "land_value_score": "Land Value Score",
        "development_potential_score": "Development Potential Score",
        "future_appreciation_index": "Future Appreciation Index",
    }

    def __init__(self):
        self._weights: np.ndarray | None = None
        self._bias: float = 0.0
        self._feature_means: np.ndarray | None = None
        self._feature_stds: np.ndarray | None = None
        self._trained = False
        self._training_locations = 0
        self._r_squared: float | None = None

    def _annualized_growth_pct(self, oldest: float, newest: float, span_days: int) -> float:
        if oldest <= 0 or newest <= 0:
            return 0.0
        years = max(span_days / 365.25, 0.5)
        return (((newest / oldest) ** (1 / years)) - 1) * 100

    def _latest_score(self, session: Session, location_id: int) -> ValuationScore | None:
        return session.scalar(
            select(ValuationScore)
            .where(ValuationScore.location_id == location_id)
            .order_by(ValuationScore.computed_at.desc(), ValuationScore.id.desc())
        )

    def _build_location_context(self, session: Session, location_id: int) -> dict:
        census = session.scalar(
            select(CensusData)
            .where(CensusData.location_id == location_id)
            .order_by(CensusData.year.desc())
        )
        density = float(census.density_per_sqkm) if census and census.density_per_sqkm else 10000
        pop_growth = float(census.growth_rate_pct) if census and census.growth_rate_pct else 3.0

        masterplan = session.scalar(
            select(Masterplan)
            .where(Masterplan.location_id == location_id)
            .order_by(Masterplan.created_at.desc())
        )
        fsi = float(masterplan.fsi) if masterplan and masterplan.fsi else 1.5

        score = self._latest_score(session, location_id)
        land_value_score = float(score.land_value_score) if score and score.land_value_score is not None else 50.0
        development_potential_score = (
            float(score.development_potential_score)
            if score and score.development_potential_score is not None
            else 50.0
        )
        future_appreciation_index = (
            float(score.future_appreciation_index)
            if score and score.future_appreciation_index is not None
            else 50.0
        )

        return {
            "density": density,
            "population_growth_pct": pop_growth,
            "fsi": fsi,
            "land_value_score": land_value_score,
            "development_potential_score": development_potential_score,
            "future_appreciation_index": future_appreciation_index,
        }

    def _compose_feature_vector(self, context: dict, *, current_price: float, trailing_growth_pct: float) -> np.ndarray:
        return np.array([
            current_price,
            trailing_growth_pct,
            context["density"],
            context["population_growth_pct"],
            context["fsi"],
            context["land_value_score"],
            context["development_potential_score"],
            context["future_appreciation_index"],
        ], dtype=float)

    def _annualized_forward_price(self, current_price: float, future_price: float, span_days: int) -> float:
        if current_price <= 0 or future_price <= 0:
            return current_price
        annualized_growth_pct = self._annualized_growth_pct(current_price, future_price, span_days)
        annualized_growth_pct = float(np.clip(annualized_growth_pct, -12.0, 24.0))
        return current_price * (1 + (annualized_growth_pct / 100))

    def _build_location_sample(self, session: Session, location_id: int) -> tuple[np.ndarray, dict] | None:
        prices = list(session.scalars(
            select(PropertyPrice)
            .where(PropertyPrice.location_id == location_id)
            .order_by(PropertyPrice.recorded_date)
        ))
        if len(prices) < 2:
            return None

        oldest = float(prices[0].price_per_sqft)
        newest = float(prices[-1].price_per_sqft)
        if oldest <= 0 or newest <= 0:
            return None

        total_span_days = max((prices[-1].recorded_date - prices[0].recorded_date).days, 30)
        trailing_span_days = max((prices[-1].recorded_date - prices[-2].recorded_date).days, 30)
        trailing_growth_pct = self._annualized_growth_pct(
            float(prices[-2].price_per_sqft),
            newest,
            trailing_span_days,
        )
        growth_pct = ((newest - oldest) / oldest) * 100
        annualized_growth_pct = self._annualized_growth_pct(oldest, newest, total_span_days)

        context = self._build_location_context(session, location_id)
        features = self._compose_feature_vector(
            context,
            current_price=newest,
            trailing_growth_pct=trailing_growth_pct,
        )
        metadata = {
            "current_avg_price": newest,
            "history_points": len(prices),
            "span_days": total_span_days,
            "historical_growth_pct": growth_pct,
            "annualized_growth_pct": annualized_growth_pct,
            "trailing_growth_pct": trailing_growth_pct,
            "population_growth_pct": context["population_growth_pct"],
            "fsi": context["fsi"],
        }
        return features, metadata

    def _extract_features(self, session: Session) -> tuple[np.ndarray, np.ndarray, list[int]]:
        """Extract feature matrix X and target vector y from database.

        Features per location:
        0. current_price
        1. trailing annualized growth
        2. density_per_sqkm
        3. growth_rate_pct (population)
        4. fsi
        5. land_value_score
        6. development_potential_score
        7. future_appreciation_index

        Target:
        annualized 1-year forward price per sqft derived from historical pairs.
        """
        locations = list(session.scalars(select(Location)))

        X_rows = []
        y_rows = []
        loc_ids = []

        for loc in locations:
            prices = list(session.scalars(
                select(PropertyPrice)
                .where(PropertyPrice.location_id == loc.id)
                .order_by(PropertyPrice.recorded_date)
            ))
            if len(prices) < 2:
                continue
            context = self._build_location_context(session, loc.id)

            for index in range(len(prices) - 1):
                current = prices[index]
                future = prices[index + 1]
                current_price = float(current.price_per_sqft)
                future_price = float(future.price_per_sqft)
                if current_price <= 0 or future_price <= 0:
                    continue

                if index == 0:
                    trailing_growth_pct = 0.0
                else:
                    previous = prices[index - 1]
                    trailing_span_days = max((current.recorded_date - previous.recorded_date).days, 30)
                    trailing_growth_pct = self._annualized_growth_pct(
                        float(previous.price_per_sqft),
                        current_price,
                        trailing_span_days,
                    )

                forward_span_days = max((future.recorded_date - current.recorded_date).days, 30)
                target_price = self._annualized_forward_price(current_price, future_price, forward_span_days)

                X_rows.append(
                    self._compose_feature_vector(
                        context,
                        current_price=current_price,
                        trailing_growth_pct=trailing_growth_pct,
                    )
                )
                y_rows.append(target_price)
                loc_ids.append(loc.id)

        return np.array(X_rows), np.array(y_rows), loc_ids

    def _normalize_features(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        """Standardize features (zero mean, unit variance)."""
        if fit:
            self._feature_means = X.mean(axis=0)
            self._feature_stds = X.std(axis=0)
            self._feature_stds[self._feature_stds == 0] = 1.0  # avoid div by zero
        return (X - self._feature_means) / self._feature_stds

    def train(self, session: Session) -> dict:
        """Train the model on all available location data."""
        X, y, loc_ids = self._extract_features(session)
        self._training_locations = len(set(loc_ids))

        if len(X) < 3:
            logger.warning("Not enough data to train (need >= 3 locations with price history)")
            self._trained = False
            self._r_squared = None
            return {"status": "insufficient_data", "locations": len(X)}

        X_norm = self._normalize_features(X, fit=True)

        # Add bias column
        X_b = np.column_stack([np.ones(len(X_norm)), X_norm])

        # Ordinary Least Squares: w = (X^T X)^-1 X^T y
        try:
            XtX = X_b.T @ X_b
            # Add small regularization to prevent singular matrix
            XtX += np.eye(XtX.shape[0]) * 1e-6
            self._weights = np.linalg.solve(XtX, X_b.T @ y)
            self._bias = self._weights[0]
            self._trained = True
        except np.linalg.LinAlgError:
            logger.error("Failed to solve linear regression — singular matrix")
            self._trained = False
            self._r_squared = None
            return {"status": "error", "message": "singular matrix"}

        # Compute R² score
        y_pred = X_b @ self._weights
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        self._r_squared = round(float(r_squared), 4)

        logger.info(
            "Model trained: R²=%.4f on %d samples across %d locations",
            r_squared,
            len(X),
            self._training_locations,
        )
        return {
            "status": "trained",
            "locations": self._training_locations,
            "r_squared": self._r_squared,
        }

    def _signal_from_upside(self, upside_pct: float) -> str:
        if upside_pct >= 12:
            return "bullish"
        if upside_pct >= 5:
            return "positive"
        if upside_pct >= 0:
            return "neutral"
        return "cautious"

    def _confidence_band(self, history_points: int, *, trained: bool) -> str:
        if not trained:
            return "low"
        if history_points >= 4 and (self._r_squared or 0) >= 0.55:
            return "high"
        if history_points >= 3 and (self._r_squared or 0) >= 0.25:
            return "medium"
        return "low"

    def _build_prediction_drivers(self, features: np.ndarray, X_norm: np.ndarray) -> list[PredictionDriver]:
        if self._weights is None:
            return []

        contributions = X_norm * self._weights[1:]
        drivers = []
        for index, key in enumerate(self.FEATURE_KEYS):
            contribution = float(contributions[index])
            if abs(contribution) < 0.0001:
                direction = "neutral"
            elif contribution > 0:
                direction = "positive"
            else:
                direction = "negative"
            drivers.append(
                PredictionDriver(
                    key=key,
                    label=self.FEATURE_LABELS[key],
                    value=round(float(features[index]), 2),
                    contribution=round(contribution, 4),
                    direction=direction,
                )
            )
        drivers.sort(key=lambda item: abs(item.contribution), reverse=True)
        return drivers[:4]

    def _fallback_growth_rate(self, metadata: dict, features: np.ndarray) -> tuple[float, list[PredictionDriver]]:
        historical_growth = float(metadata["annualized_growth_pct"])
        population_growth = float(metadata["population_growth_pct"])
        fsi = float(metadata["fsi"])
        future_appreciation = float(features[7])
        predicted_growth = (
            (historical_growth * 0.55)
            + (population_growth * 0.20)
            + ((fsi - 1.5) * 2.5)
            + ((future_appreciation - 50) * 0.05)
        )
        predicted_growth = float(np.clip(predicted_growth, -6.0, 18.0))
        drivers = [
            PredictionDriver(
                key="historical_growth_pct",
                label=self.FEATURE_LABELS["historical_growth_pct"],
                value=round(float(metadata["historical_growth_pct"]), 2),
                contribution=round(float(metadata["annualized_growth_pct"] * 0.55), 4),
                direction="positive" if metadata["annualized_growth_pct"] >= 0 else "negative",
            ),
            PredictionDriver(
                key="population_growth_pct",
                label=self.FEATURE_LABELS["population_growth_pct"],
                value=round(population_growth, 2),
                contribution=round(population_growth * 0.20, 4),
                direction="positive" if population_growth >= 0 else "negative",
            ),
            PredictionDriver(
                key="future_appreciation_index",
                label=self.FEATURE_LABELS["future_appreciation_index"],
                value=round(future_appreciation, 2),
                contribution=round((future_appreciation - 50) * 0.05, 4),
                direction="positive" if future_appreciation >= 50 else "negative",
            ),
        ]
        return predicted_growth, drivers

    def predict(self, session: Session, location_id: int) -> PricePrediction | None:
        """Predict future prices for a specific location."""
        loc = session.get(Location, location_id)
        if not loc:
            return None

        sample = self._build_location_sample(session, location_id)
        if sample is None:
            return None
        features, metadata = sample

        trained = self._trained
        if not self._trained:
            train_result = self.train(session)
            trained = train_result["status"] == "trained"

        current_price = float(metadata["current_avg_price"])
        if trained and self._weights is not None:
            X_norm = self._normalize_features(np.array([features], dtype=float))
            X_b = np.column_stack([np.ones(1), X_norm])
            predicted_next = float((X_b @ self._weights).item())
            drivers = self._build_prediction_drivers(features, X_norm[0])
            model_version = self.MODEL_VERSION
        else:
            predicted_growth, drivers = self._fallback_growth_rate(metadata, features)
            predicted_next = current_price * (1 + (predicted_growth / 100))
            model_version = self.FALLBACK_MODEL_VERSION

        predicted_next = float(np.clip(predicted_next, current_price * 0.75, current_price * 1.40))
        predicted_growth = ((predicted_next / current_price) - 1) * 100 if current_price > 0 else 0.0
        predicted_3yr = current_price * ((1 + (predicted_growth / 100)) ** 3)
        predicted_3yr = max(predicted_3yr, current_price * 0.70)

        predicted_upside_pct = ((predicted_next / current_price) - 1) * 100 if current_price > 0 else 0.0
        signal = self._signal_from_upside(predicted_upside_pct)
        confidence = self._confidence_band(int(metadata["history_points"]), trained=trained)
        leading_drivers = ", ".join(driver.label for driver in drivers[:2]) or "historical trend"

        return PricePrediction(
            location_id=location_id,
            location_name=loc.name,
            current_avg_price=round(current_price, 2),
            predicted_price_1yr=round(predicted_next, 2),
            predicted_price_3yr=round(predicted_3yr, 2),
            annual_growth_pct=round(predicted_growth, 2),
            confidence=confidence,
            predicted_upside_pct=round(predicted_upside_pct, 2),
            signal=signal,
            model_version=model_version,
            training_locations=self._training_locations,
            r_squared=self._r_squared,
            drivers=drivers,
            summary=(
                f"{signal.title()} ML outlook with {predicted_upside_pct:.2f}% projected 1Y upside. "
                f"Top drivers: {leading_drivers}."
            ),
        )
