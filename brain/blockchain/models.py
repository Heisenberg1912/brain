from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brain.database import Base


class ArchitecturalPlan(Base):
    __tablename__ = "architectural_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(String(150))
    author_wallet: Mapped[str] = mapped_column(String(120))
    current_owner_wallet: Mapped[str] = mapped_column(String(120))
    version_label: Mapped[str] = mapped_column(String(50), default="v1")
    file_hash: Mapped[str] = mapped_column(String(255), unique=True)
    preview_url: Mapped[str | None] = mapped_column(String(500))
    storage_uri: Mapped[str | None] = mapped_column(String(500))
    ipfs_cid: Mapped[str | None] = mapped_column(String(255))
    license_code: Mapped[str] = mapped_column(String(50), default="custom")
    asset_status: Mapped[str] = mapped_column(String(50), default="draft")
    personal_license_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    commercial_license_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    resale_license_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    royalty_bps: Mapped[int] = mapped_column(Integer, default=500)
    chain: Mapped[str | None] = mapped_column(String(50))
    contract_address: Mapped[str | None] = mapped_column(String(255))
    token_id: Mapped[str | None] = mapped_column(String(120))
    mint_tx_hash: Mapped[str | None] = mapped_column(String(255))
    minted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rights_metadata: Mapped[dict | None] = mapped_column(JSONB)
    constraint_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    zoning_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    location_intelligence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    massing_inputs: Mapped[dict | None] = mapped_column(JSONB)
    mint_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped["Location"] = relationship(back_populates="plans")
    licenses: Mapped[list["PlanLicense"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    ledger_events: Mapped[list["PlanLedgerEvent"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    exchange_listings: Mapped[list["ExchangeListing"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class PlanLicense(Base):
    __tablename__ = "plan_licenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("architectural_plans.id"))
    grantee_wallet: Mapped[str] = mapped_column(String(120))
    grantee_name: Mapped[str | None] = mapped_column(String(150))
    personal_use: Mapped[bool] = mapped_column(Boolean, default=True)
    commercial_use: Mapped[bool] = mapped_column(Boolean, default=False)
    resale_use: Mapped[bool] = mapped_column(Boolean, default=False)
    can_sublicense: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    note: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped["ArchitecturalPlan"] = relationship(back_populates="licenses")


class PlanLedgerEvent(Base):
    __tablename__ = "plan_ledger_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("architectural_plans.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    actor_wallet: Mapped[str | None] = mapped_column(String(120))
    from_wallet: Mapped[str | None] = mapped_column(String(120))
    to_wallet: Mapped[str | None] = mapped_column(String(120))
    tx_hash: Mapped[str | None] = mapped_column(String(255))
    chain: Mapped[str | None] = mapped_column(String(50))
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(20))
    event_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped["ArchitecturalPlan"] = relationship(back_populates="ledger_events")


class ExchangeListing(Base):
    __tablename__ = "exchange_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("architectural_plans.id"))
    seller_wallet: Mapped[str] = mapped_column(String(120))
    listing_type: Mapped[str] = mapped_column(String(50), default="sale")
    asking_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(20), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="active")
    personal_use: Mapped[bool] = mapped_column(Boolean, default=True)
    commercial_use: Mapped[bool] = mapped_column(Boolean, default=False)
    resale_use: Mapped[bool] = mapped_column(Boolean, default=False)
    can_sublicense: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    plan: Mapped["ArchitecturalPlan"] = relationship(back_populates="exchange_listings")
    offers: Mapped[list["ExchangeOffer"]] = relationship(back_populates="listing", cascade="all, delete-orphan")


class ExchangeOffer(Base):
    __tablename__ = "exchange_offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("exchange_listings.id"))
    bidder_wallet: Mapped[str] = mapped_column(String(120))
    bidder_name: Mapped[str | None] = mapped_column(String(150))
    offer_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(20), default="USD")
    intended_use: Mapped[str] = mapped_column(String(50), default="personal")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listing: Mapped["ExchangeListing"] = relationship(back_populates="offers")


class TokenizedProperty(Base):
    __tablename__ = "tokenized_properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    asset_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    issuer_name: Mapped[str] = mapped_column(String(150))
    issuer_wallet: Mapped[str] = mapped_column(String(120))
    property_type: Mapped[str | None] = mapped_column(String(80))
    asset_ref: Mapped[str | None] = mapped_column(String(120), unique=True)
    fractional_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    total_units: Mapped[int] = mapped_column(Integer, default=1)
    valuation_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(20), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="active")
    chain: Mapped[str | None] = mapped_column(String(50))
    contract_address: Mapped[str | None] = mapped_column(String(255))
    token_symbol: Mapped[str | None] = mapped_column(String(20))
    token_standard: Mapped[str | None] = mapped_column(String(50))
    tokenization_tx_hash: Mapped[str | None] = mapped_column(String(255))
    asset_metadata: Mapped[dict | None] = mapped_column(JSONB)
    rights_metadata: Mapped[dict | None] = mapped_column(JSONB)
    tokenized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    location: Mapped["Location"] = relationship(back_populates="tokenized_properties")
    allocations: Mapped[list["PropertyTokenAllocation"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    ledger_events: Mapped[list["PropertyLedgerEvent"]] = relationship(back_populates="property", cascade="all, delete-orphan")


class PropertyTokenAllocation(Base):
    __tablename__ = "property_token_allocations"
    __table_args__ = (
        UniqueConstraint("property_id", "wallet", name="uq_property_token_allocations_property_wallet"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("tokenized_properties.id"))
    wallet: Mapped[str] = mapped_column(String(120))
    holder_name: Mapped[str | None] = mapped_column(String(150))
    units_owned: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    property: Mapped["TokenizedProperty"] = relationship(back_populates="allocations")


class PropertyLedgerEvent(Base):
    __tablename__ = "property_ledger_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("tokenized_properties.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    actor_wallet: Mapped[str | None] = mapped_column(String(120))
    from_wallet: Mapped[str | None] = mapped_column(String(120))
    to_wallet: Mapped[str | None] = mapped_column(String(120))
    tx_hash: Mapped[str | None] = mapped_column(String(255))
    chain: Mapped[str | None] = mapped_column(String(50))
    units: Mapped[int | None] = mapped_column(Integer)
    consideration_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(20))
    event_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    property: Mapped["TokenizedProperty"] = relationship(back_populates="ledger_events")
