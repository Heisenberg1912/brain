from datetime import date, datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    country_code: Mapped[str] = mapped_column(String(2), default="IN")
    state: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100), default="Unknown")
    locality: Mapped[str | None] = mapped_column(String(200))
    ward: Mapped[str | None] = mapped_column(String(100))
    pin_code: Mapped[str | None] = mapped_column(String(10))
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    masterplans: Mapped[list["Masterplan"]] = relationship(back_populates="location")
    prices: Mapped[list["PropertyPrice"]] = relationship(back_populates="location")
    census: Mapped[list["CensusData"]] = relationship(back_populates="location")
    geo_profiles: Mapped[list["LocationGeoProfile"]] = relationship(back_populates="location")
    scores: Mapped[list["ValuationScore"]] = relationship(back_populates="location")
    planning_contexts: Mapped[list["PlanningContext"]] = relationship(back_populates="location")
    plans: Mapped[list["ArchitecturalPlan"]] = relationship(back_populates="location")
    tokenized_properties: Mapped[list["TokenizedProperty"]] = relationship(back_populates="location")
    tokenized_properties: Mapped[list["TokenizedProperty"]] = relationship(back_populates="location")

    __table_args__ = (
        Index("idx_locations_geom", "geom", postgresql_using="gist"),
    )


class Masterplan(Base):
    __tablename__ = "masterplans"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    version: Mapped[str] = mapped_column(String(50), default="BDA_RMP_2031")
    dataset_version: Mapped[str] = mapped_column(String(50), default="seed_v1")
    zoning_type: Mapped[str | None] = mapped_column(String(100))
    fsi: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    ground_coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    max_height_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    setback_front_m: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    setback_side_m: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    approval_status: Mapped[str] = mapped_column(String(50), default="active")
    source_url: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped["Location"] = relationship(back_populates="masterplans")


class PropertyPrice(Base):
    __tablename__ = "property_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    price_per_sqft: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    property_type: Mapped[str | None] = mapped_column(String(50))
    recorded_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list | dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped["Location"] = relationship(back_populates="prices")


class Infrastructure(Base):
    __tablename__ = "infrastructure"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    infra_type: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str] = mapped_column(String(2), default="IN")
    state: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100), default="Unknown")
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list | dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_infra_geom", "geom", postgresql_using="gist"),
    )


class CensusData(Base):
    __tablename__ = "census_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    year: Mapped[int] = mapped_column(Integer)
    population: Mapped[int | None] = mapped_column(Integer)
    density_per_sqkm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    growth_rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    households: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list | dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped["Location"] = relationship(back_populates="census")


class LocationGeoProfile(Base):
    __tablename__ = "location_geo_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    dataset_version: Mapped[str] = mapped_column(String(50), default="seed_v1")
    terrain_class: Mapped[str | None] = mapped_column(String(50))
    terrain_slope_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    flood_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    heat_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    climate_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    road_proximity_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    transit_proximity_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    source: Mapped[str | None] = mapped_column(String(120))
    tags: Mapped[list | dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped["Location"] = relationship(back_populates="geo_profiles")


class RegionalStandard(Base):
    __tablename__ = "regional_standards"

    id: Mapped[int] = mapped_column(primary_key=True)
    standard_type: Mapped[str] = mapped_column(String(50))
    country_code: Mapped[str] = mapped_column(String(2), default="IN")
    admin_area: Mapped[str | None] = mapped_column(String(120))
    region_name: Mapped[str | None] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    version_tag: Mapped[str] = mapped_column(String(50), default="v1")
    source_url: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | dict | None] = mapped_column(JSONB)
    rules: Mapped[dict | None] = mapped_column(JSONB)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_regional_standards_scope", "country_code", "admin_area", "standard_type"),
    )


class PlanningContext(Base):
    __tablename__ = "planning_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    version_tag: Mapped[str] = mapped_column(String(50), default="v1")
    country_code: Mapped[str] = mapped_column(String(2), default="IN")
    admin_area: Mapped[str | None] = mapped_column(String(120))
    market_tier: Mapped[str | None] = mapped_column(String(50))
    validation_status: Mapped[str] = mapped_column(String(50), default="draft")
    floor_plan_constraints: Mapped[dict | None] = mapped_column(JSONB)
    zoning_validation_rules: Mapped[dict | None] = mapped_column(JSONB)
    location_intelligence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    massing_inputs: Mapped[dict | None] = mapped_column(JSONB)
    source_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    location: Mapped["Location"] = relationship(back_populates="planning_contexts")


# Import dependent models so SQLAlchemy can resolve string relationships
from brain.blockchain.models import ArchitecturalPlan, TokenizedProperty  # noqa: E402,F401
from brain.valuation.models import ValuationScore  # noqa: E402,F401
