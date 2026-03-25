from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.database import Base


class ValuationScore(Base):
    __tablename__ = "valuation_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    land_value_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    development_potential_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    future_appreciation_index: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    infra_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    price_trend_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    zoning_favorability: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    density_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    weights: Mapped[dict | None] = mapped_column(JSONB)

    location: Mapped["Location"] = relationship(back_populates="scores")
