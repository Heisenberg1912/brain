"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from brain.config import settings


SUPPORTED_CHAIN_CHOICES = tuple(item.strip().lower() for item in settings.supported_plan_chains.split(",") if item.strip())
DEFAULT_CHAIN = settings.default_plan_chain.strip().lower()


def _validate_supported_chain(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_CHAIN_CHOICES:
        raise ValueError(f"chain must be one of: {', '.join(SUPPORTED_CHAIN_CHOICES)}")
    return normalized


# Data Bank

class LocationOut(BaseModel):
    id: int
    name: str
    country_code: str = "IN"
    state: str | None = None
    city: str | None = None
    locality: str | None = None
    ward: str | None = None
    pin_code: str | None = None
    lat: float | None = None
    lng: float | None = None
    zoning_type: str | None = "residential"


class LocationWithDistance(LocationOut):
    distance_km: float


class MasterplanOut(BaseModel):
    zoning_type: str | None = None
    fsi: float | None = None
    ground_coverage_pct: float | None = None
    max_height_m: float | None = None
    setback_front_m: float | None = None
    setback_side_m: float | None = None
    version: str | None = None
    dataset_version: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    approval_status: str | None = None
    tags: list[str] = []


class PriceOut(BaseModel):
    price_per_sqft: float
    property_type: str | None = None
    recorded_date: str
    source: str | None = None
    tags: list[str] = []


class InfrastructureOut(BaseModel):
    id: int
    name: str
    infra_type: str
    country_code: str = "IN"
    state: str | None = None
    city: str | None = None
    status: str | None = None
    lat: float | None = None
    lng: float | None = None
    tags: list[str] = []


class NearbyInfraOut(BaseModel):
    name: str
    infra_type: str
    status: str | None = None
    distance_km: float


class NearbyInfraGeo(BaseModel):
    id: int
    name: str
    infra_type: str
    status: str | None = None
    lat: float | None = None
    lng: float | None = None
    distance_km: float


class CensusOut(BaseModel):
    year: int
    population: int | None = None
    density_per_sqkm: float | None = None
    growth_rate_pct: float | None = None
    households: int | None = None
    tags: list[str] = []


class GeoProfileOut(BaseModel):
    terrain_class: str | None = None
    terrain_slope_pct: float | None = None
    flood_risk_score: float | None = None
    heat_risk_score: float | None = None
    climate_risk_score: float | None = None
    road_proximity_km: float | None = None
    transit_proximity_km: float | None = None
    dataset_version: str | None = None
    source: str | None = None
    tags: list[str] = []


class RegionalStandardOut(BaseModel):
    id: int
    standard_type: str
    country_code: str
    admin_area: str | None = None
    region_name: str | None = None
    code: str
    title: str
    version_tag: str
    source_url: str | None = None
    tags: list[str] = []
    rules: dict = Field(default_factory=dict)


class LocationSummary(BaseModel):
    location: LocationOut
    masterplan: MasterplanOut | None = None
    avg_price_per_sqft: float | None = None
    price_history: list[PriceOut] = []
    census: CensusOut | None = None
    geo_profile: GeoProfileOut | None = None
    regional_standards: list[RegionalStandardOut] = []
    nearby_infrastructure: list[NearbyInfraOut] = []


class LocationIntelligenceOut(BaseModel):
    location_id: int
    location_name: str
    city: str | None = None
    zoning_type: str | None = None
    fsi: float | None = None
    avg_price_per_sqft: float | None = None
    land_value_score: float | None = None
    development_potential_score: float | None = None
    future_appreciation_index: float | None = None
    density_score: float | None = None
    infra_score: float | None = None
    price_trend_score: float | None = None
    climate_resilience_score: float | None = None
    terrain_readiness_score: float | None = None
    population: int | None = None
    growth_rate_pct: float | None = None
    terrain_class: str | None = None
    terrain_slope_pct: float | None = None
    flood_risk_score: float | None = None
    heat_risk_score: float | None = None
    climate_risk_score: float | None = None
    predicted_price_1yr: float | None = None
    predicted_price_3yr: float | None = None
    prediction_confidence: float | None = None
    planning_context_id: int | None = None
    planning_context_version: str | None = None
    data_confidence_score: float | None = None
    data_confidence_band: str | None = None
    data_gaps: list[str] = Field(default_factory=list)
    regional_standards: list[str] = []
    masterplan_version: str | None = None
    masterplan_dataset_version: str | None = None


class PlanningContextCreate(BaseModel):
    location_id: int
    version_tag: str = Field(default="v1", min_length=1, max_length=50)
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    admin_area: str | None = None
    market_tier: str | None = None
    validation_status: str = Field(default="draft", min_length=1, max_length=50)
    floor_plan_constraints: dict = Field(default_factory=dict)
    zoning_validation_rules: dict = Field(default_factory=dict)
    location_intelligence_score: float | None = Field(default=None, ge=0, le=100)
    massing_inputs: dict = Field(default_factory=dict)
    source_summary: str | None = None


class PlanningContextOut(BaseModel):
    id: int
    location_id: int
    version_tag: str
    country_code: str
    admin_area: str | None = None
    market_tier: str | None = None
    validation_status: str
    floor_plan_constraints: dict = Field(default_factory=dict)
    zoning_validation_rules: dict = Field(default_factory=dict)
    location_intelligence_score: float | None = None
    massing_inputs: dict = Field(default_factory=dict)
    source_summary: str | None = None


# Valuation

class ScoreComponents(BaseModel):
    infra_score: float
    price_trend_score: float
    zoning_favorability: float
    road_access_score: float | None = None
    metro_access_score: float | None = None
    economic_access_score: float | None = None
    strategic_infra_score: float | None = None
    density_score: float
    population_growth_score: float | None = None
    demand_pressure_score: float | None = None
    zoning_shift_score: float | None = None
    annualized_growth_pct: float | None = None
    recent_12m_growth_pct: float | None = None
    climate_exposure_score: float | None = None
    climate_resilience_score: float | None = None
    terrain_constraint_score: float | None = None
    terrain_readiness_score: float | None = None
    site_risk_score: float | None = None
    avg_price_per_sqft: float | None = None
    data_confidence_score: float | None = None
    data_confidence_band: str | None = None
    score_calibration_factor: float | None = None


class ScoreOut(BaseModel):
    location: str
    location_id: int
    land_value_score: float
    development_potential_score: float
    future_appreciation_index: float
    components: ScoreComponents


class RankingItem(BaseModel):
    rank: int
    location: str
    location_id: int
    land_value_score: float
    development_potential_score: float
    future_appreciation_index: float
    zoning_type: str | None = "residential"


class CompareRequest(BaseModel):
    location_ids: list[int] = Field(..., min_length=1, max_length=20)


class PredictionDriverOut(BaseModel):
    key: str
    label: str
    value: float
    contribution: float
    direction: Literal["positive", "negative", "neutral"]


class PricePredictionOut(BaseModel):
    location_id: int
    location_name: str
    current_avg_price: float
    predicted_price_1yr: float
    predicted_price_3yr: float
    annual_growth_pct: float
    confidence: str
    predicted_upside_pct: float
    signal: Literal["bullish", "positive", "neutral", "cautious"]
    model_version: str
    training_locations: int
    r_squared: float | None = None
    drivers: list[PredictionDriverOut] = Field(default_factory=list)
    summary: str


class HotspotFeatureOut(BaseModel):
    key: str
    label: str
    average: float
    delta_from_baseline: float
    relative_level: Literal["high", "low", "neutral"]


class HotspotOut(BaseModel):
    cluster_id: int
    label: str
    summary: str
    cluster_size: int
    hotspot_score: float
    dominant_signal: str
    locations: list[dict]
    avg_land_value: float
    avg_development_potential: float
    avg_appreciation: float
    avg_infra_score: float
    avg_price_trend: float
    avg_price: float
    feature_profile: list[HotspotFeatureOut] = Field(default_factory=list)


class ValuationCoverageOut(BaseModel):
    evidence_score: float = 0.0
    confidence_band: str = "low"
    score_calibration_factor: float = 1.0
    data_gaps: list[str] = Field(default_factory=list)
    masterplan_present: bool = False
    masterplan_history_count: int = 0
    price_history_points: int = 0
    price_history_span_days: int = 0
    latest_price_age_days: int | None = None
    census_present: bool = False
    geo_profile_present: bool = False
    nearby_infra_count: int = 0
    regional_standard_count: int = 0


class ValuationMarketInputsOut(BaseModel):
    avg_price_per_sqft: float | None = None
    oldest_price_per_sqft: float | None = None
    latest_price_per_sqft: float | None = None
    price_growth_pct: float | None = None
    annualized_growth_pct: float | None = None
    recent_12m_growth_pct: float | None = None
    first_recorded_date: str | None = None
    latest_recorded_date: str | None = None
    price_history_span_days: int = 0
    price_history_points: int
    price_trend_direction: str | None = None
    price_momentum_band: str | None = None


class ValuationPlanningInputsOut(BaseModel):
    zoning_type: str | None = None
    approval_status: str | None = None
    fsi: float | None = None
    max_height_m: float | None = None
    ground_coverage_pct: float | None = None
    masterplan_version: str | None = None
    masterplan_history_count: int = 0
    previous_zoning_type: str | None = None
    zoning_shift_direction: str | None = None
    zoning_shift_summary: str | None = None
    zoning_shift_effective_from: str | None = None
    zoning_shift_score: float | None = None
    market_tier: str | None = None
    validation_status: str | None = None
    planning_context_version: str | None = None
    location_intelligence_score: float | None = None
    regional_standard_codes: list[str] = Field(default_factory=list)


class ValuationDemandInputsOut(BaseModel):
    population: int | None = None
    growth_rate_pct: float | None = None
    density_per_sqkm: float | None = None
    density_score: float | None = None
    population_growth_score: float | None = None
    demand_pressure_score: float | None = None
    demand_profile: str | None = None


class ValuationInfrastructureInputsOut(BaseModel):
    nearby_infra_count: int
    planned_infra_count: int
    transit_node_count: int
    nearest_infra_km: float | None = None
    nearest_transit_node_km: float | None = None
    road_proximity_km: float | None = None
    metro_proximity_km: float | None = None
    economic_zone_proximity_km: float | None = None
    road_access_score: float | None = None
    metro_access_score: float | None = None
    economic_access_score: float | None = None
    strategic_infra_score: float | None = None
    metro_station_count: int = 0
    economic_zone_count: int = 0
    highway_count: int = 0
    dominant_types: list[str] = Field(default_factory=list)


class ValuationSiteInputsOut(BaseModel):
    terrain_class: str | None = None
    terrain_slope_pct: float | None = None
    road_proximity_km: float | None = None
    transit_proximity_km: float | None = None
    flood_risk_score: float | None = None
    heat_risk_score: float | None = None
    climate_risk_score: float | None = None
    climate_exposure_score: float | None = None
    terrain_constraint_score: float | None = None
    site_risk_score: float | None = None
    site_risk_band: str | None = None


class ValuationModelInputsOut(BaseModel):
    infra_score: float | None = None
    price_trend_score: float | None = None
    annualized_growth_pct: float | None = None
    recent_12m_growth_pct: float | None = None
    zoning_favorability: float | None = None
    road_access_score: float | None = None
    metro_access_score: float | None = None
    economic_access_score: float | None = None
    strategic_infra_score: float | None = None
    density_score: float | None = None
    population_growth_score: float | None = None
    demand_pressure_score: float | None = None
    zoning_shift_score: float | None = None
    climate_exposure_score: float | None = None
    climate_resilience_score: float | None = None
    terrain_constraint_score: float | None = None
    terrain_readiness_score: float | None = None
    site_risk_score: float | None = None
    planned_infra_count: int


class ValuationInputSnapshotOut(BaseModel):
    coverage: ValuationCoverageOut = Field(default_factory=ValuationCoverageOut)
    market: ValuationMarketInputsOut
    planning: ValuationPlanningInputsOut
    demand: ValuationDemandInputsOut
    infrastructure: ValuationInfrastructureInputsOut
    site: ValuationSiteInputsOut
    model_inputs: ValuationModelInputsOut


class ValuationInputsOut(ValuationInputSnapshotOut):
    location: str
    location_id: int


class ValuationCoreScoresOut(BaseModel):
    land_value_score: float
    development_potential_score: float
    future_appreciation_index: float
    overall_favorability_score: float
    strategic_infra_score: float
    demand_pressure_score: float
    site_risk_score: float


class ValuationDriverOut(BaseModel):
    key: str
    label: str
    value: float | None = None


class ValuationCoreMetricOut(BaseModel):
    score: float
    band: str
    summary: str
    drivers: list[ValuationDriverOut] = Field(default_factory=list)


class ValuationForwardOutlookOut(BaseModel):
    current_avg_price: float
    predicted_price_1yr: float
    predicted_price_3yr: float
    predicted_upside_pct: float
    annual_growth_pct: float
    signal: Literal["bullish", "positive", "neutral", "cautious"]
    confidence: str | None = None
    model_version: str | None = None
    summary: str
    drivers: list[PredictionDriverOut] = Field(default_factory=list)


class ValuationLogicRuleOut(BaseModel):
    code: str
    effect: Literal["positive", "negative", "neutral"]
    detail: str


class ValuationLogicWeightOut(BaseModel):
    key: str
    label: str
    value: float
    weight: float
    contribution: float


class ValuationLogicOut(BaseModel):
    weighted_score: float
    weighted_band: str
    investment_signal: Literal["acquire", "accumulate", "watch", "avoid"]
    execution_strategy: Literal["build_now", "entitle_then_build", "land_bank", "de_risk_first", "monitor"]
    conviction: Literal["high", "medium", "low"]
    data_confidence_score: float | None = None
    data_confidence_band: str | None = None
    primary_driver: str
    gating_issue: str | None = None
    verdict: str
    weighted_components: list[ValuationLogicWeightOut] = Field(default_factory=list)
    rule_hits: list[ValuationLogicRuleOut] = Field(default_factory=list)


class ValuationLogicResponseOut(BaseModel):
    location: str
    location_id: int
    logic: ValuationLogicOut


class ValuationCorePositioningOut(BaseModel):
    recommended_use_case: Literal["residential", "commercial", "mixed_use", "industrial"]
    favorability_band: str
    market_tier: str | None = None
    price_trend_direction: str | None = None
    price_momentum_band: str | None = None
    demand_profile: str | None = None
    site_risk_band: str | None = None
    zoning_shift_direction: str | None = None


class ValuationCoreOut(BaseModel):
    location: str
    location_id: int
    summary: str
    key_insight: str
    forward_outlook: ValuationForwardOutlookOut | None = None
    coverage: ValuationCoverageOut = Field(default_factory=ValuationCoverageOut)
    scores: ValuationCoreScoresOut
    land_value: ValuationCoreMetricOut
    development_potential: ValuationCoreMetricOut
    future_appreciation: ValuationCoreMetricOut
    logic: ValuationLogicOut
    positioning: ValuationCorePositioningOut
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)


class FavorabilityComponentsOut(BaseModel):
    market_momentum_score: float
    site_readiness_score: float
    regulatory_clarity_score: float
    mobility_score: float
    strategic_infra_score: float
    demand_pressure_score: float
    site_risk_score: float
    climate_resilience_score: float
    terrain_readiness_score: float
    data_confidence_score: float | None = None
    data_confidence_band: str | None = None


class FavorabilityUseCaseOut(BaseModel):
    residential: float
    commercial: float
    mixed_use: float
    industrial: float


class FavorabilityOut(BaseModel):
    location: str
    location_id: int
    overall_favorability_score: float
    favorability_band: str
    recommended_use_case: Literal["residential", "commercial", "mixed_use", "industrial"]
    market_tier: str | None = None
    inputs: ValuationInputSnapshotOut
    components: FavorabilityComponentsOut
    use_case_scores: FavorabilityUseCaseOut
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    valuation: ScoreOut


class FavorabilityRankingItem(BaseModel):
    rank: int
    location: str
    location_id: int
    overall_favorability_score: float
    selected_score: float
    selected_use_case: Literal["overall", "residential", "commercial", "mixed_use", "industrial"]
    recommended_use_case: Literal["residential", "commercial", "mixed_use", "industrial"]
    favorability_band: str


class SupportedChainOut(BaseModel):
    key: str
    label: str
    is_default: bool
    supports_fractional: bool
    supports_plan_nfts: bool
    positioning: str


class ContractTemplateOut(BaseModel):
    key: str
    name: str
    standard: str
    asset_type: str
    upgradable: bool
    on_chain_scope: list[str] = Field(default_factory=list)
    off_chain_scope: list[str] = Field(default_factory=list)
    source_path: str


class ContractProfileOut(BaseModel):
    philosophy: str
    default_network: str
    storage_backend: str
    principles: list[str] = Field(default_factory=list)
    templates: list[ContractTemplateOut] = Field(default_factory=list)


class StorageProfileOut(BaseModel):
    backend: str
    provider: str
    gateway_base: str
    uri_scheme: str
    upload_mode: str


# Blockchain / Rights

class ArchitecturalPlanCreate(BaseModel):
    location_id: int | None = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    author_name: str = Field(..., min_length=1, max_length=150)
    author_wallet: str = Field(..., min_length=3, max_length=120)
    version_label: str = Field(default="v1", min_length=1, max_length=50)
    file_hash: str = Field(..., min_length=8, max_length=255)
    preview_url: str | None = None
    storage_uri: str | None = None
    ipfs_cid: str | None = None
    license_code: str = Field(default="custom", min_length=1, max_length=50)
    asset_status: str = Field(default="draft", min_length=1, max_length=50)
    personal_license_allowed: bool = True
    commercial_license_allowed: bool = False
    resale_license_allowed: bool = False
    royalty_bps: int = Field(default=500, ge=0, le=10000)
    rights_metadata: dict = Field(default_factory=dict)
    constraint_snapshot: dict = Field(default_factory=dict)
    zoning_snapshot: dict = Field(default_factory=dict)
    location_intelligence_score: float | None = Field(default=None, ge=0, le=100)
    massing_inputs: dict = Field(default_factory=dict)


class ArchitecturalPlanOut(BaseModel):
    id: int
    location_id: int | None = None
    title: str
    description: str | None = None
    author_name: str
    author_wallet: str
    current_owner_wallet: str
    version_label: str
    file_hash: str
    preview_url: str | None = None
    storage_uri: str | None = None
    ipfs_cid: str | None = None
    storage_backend: str | None = None
    storage_gateway_url: str | None = None
    license_code: str
    asset_status: str
    personal_license_allowed: bool
    commercial_license_allowed: bool
    resale_license_allowed: bool
    royalty_bps: int
    chain: str | None = None
    contract_address: str | None = None
    token_id: str | None = None
    mint_tx_hash: str | None = None
    rights_metadata: dict = Field(default_factory=dict)
    constraint_snapshot: dict = Field(default_factory=dict)
    zoning_snapshot: dict = Field(default_factory=dict)
    location_intelligence_score: float | None = None
    massing_inputs: dict = Field(default_factory=dict)
    mint_metadata: dict = Field(default_factory=dict)


class PlanLicenseCreate(BaseModel):
    grantee_wallet: str = Field(..., min_length=3, max_length=120)
    grantee_name: str | None = None
    personal_use: bool = True
    commercial_use: bool = False
    resale_use: bool = False
    can_sublicense: bool = False
    status: str = Field(default="active", min_length=1, max_length=50)
    note: str | None = None
    expires_at: datetime | None = None


class PlanLicenseOut(BaseModel):
    id: int
    plan_id: int
    grantee_wallet: str
    grantee_name: str | None = None
    personal_use: bool
    commercial_use: bool
    resale_use: bool
    can_sublicense: bool
    status: str
    note: str | None = None
    expires_at: datetime | None = None


class MintPlanRequest(BaseModel):
    chain: str = Field(..., min_length=1, max_length=50)
    contract_address: str = Field(..., min_length=6, max_length=255)
    token_id: str = Field(..., min_length=1, max_length=120)
    tx_hash: str | None = None
    minted_by_wallet: str | None = None

    @field_validator("chain")
    @classmethod
    def validate_chain(cls, value: str) -> str:
        normalized = _validate_supported_chain(value)
        if normalized is None:
            raise ValueError("chain is required")
        return normalized


class PlanTransferRequest(BaseModel):
    transferred_by_wallet: str = Field(..., min_length=3, max_length=120)
    to_wallet: str = Field(..., min_length=3, max_length=120)
    transfer_type: str = Field(default="transfer", min_length=1, max_length=50)
    sale_price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=20)
    tx_hash: str | None = None


class PlanTransferResponse(BaseModel):
    plan_id: int
    new_owner_wallet: str
    royalty_due: float


class ExchangeListingCreate(BaseModel):
    plan_id: int
    seller_wallet: str = Field(..., min_length=3, max_length=120)
    listing_type: Literal["sale", "license"] = "sale"
    asking_price: float = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=1, max_length=20)
    personal_use: bool = True
    commercial_use: bool = False
    resale_use: bool = False
    can_sublicense: bool = False
    note: str | None = None
    expires_at: datetime | None = None


class ExchangeListingOut(BaseModel):
    id: int
    plan_id: int
    seller_wallet: str
    listing_type: str
    asking_price: float
    currency: str
    status: str
    personal_use: bool
    commercial_use: bool
    resale_use: bool
    can_sublicense: bool
    note: str | None = None
    expires_at: datetime | None = None


class ExchangeOfferCreate(BaseModel):
    bidder_wallet: str = Field(..., min_length=3, max_length=120)
    bidder_name: str | None = None
    offer_price: float = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=1, max_length=20)
    intended_use: Literal["personal", "commercial", "resale"] = "personal"
    note: str | None = None


class ExchangeOfferOut(BaseModel):
    id: int
    listing_id: int
    bidder_wallet: str
    bidder_name: str | None = None
    offer_price: float
    currency: str
    intended_use: str
    status: str
    note: str | None = None


class AcceptExchangeOfferRequest(BaseModel):
    accepted_by_wallet: str = Field(..., min_length=3, max_length=120)
    tx_hash: str | None = None


class AcceptExchangeOfferResponse(BaseModel):
    listing_id: int
    offer_id: int
    mode: str
    royalty_due: float
    license_id: int | None = None
    new_owner_wallet: str | None = None


class CancelExchangeListingRequest(BaseModel):
    cancelled_by_wallet: str = Field(..., min_length=3, max_length=120)


class PlanLedgerEventOut(BaseModel):
    id: int
    plan_id: int
    event_type: str
    actor_wallet: str | None = None
    from_wallet: str | None = None
    to_wallet: str | None = None
    tx_hash: str | None = None
    chain: str | None = None
    sale_price: float | None = None
    currency: str | None = None
    event_metadata: dict = Field(default_factory=dict)


class UsageRightsCheckRequest(BaseModel):
    wallet: str = Field(..., min_length=3, max_length=120)
    intended_use: Literal["personal", "commercial", "resale"]


class UsageRightsCheckResponse(BaseModel):
    plan_id: int
    wallet: str
    intended_use: str
    allowed: bool
    basis: str
    license_id: int | None = None
    reason: str
    royalty_bps: int


class TokenMetadataAttributeOut(BaseModel):
    trait_type: str
    value: str | int | float | bool | None


class TokenMetadataOut(BaseModel):
    name: str
    description: str | None = None
    image: str | None = None
    external_url: str | None = None
    attributes: list[TokenMetadataAttributeOut] = Field(default_factory=list)
    properties: dict = Field(default_factory=dict)


class PlanStorageAttachRequest(BaseModel):
    ipfs_cid: str | None = Field(default=None, min_length=10, max_length=255)
    storage_uri: str | None = Field(default=None, min_length=8, max_length=500)
    preview_url: str | None = None
    attached_by_wallet: str | None = Field(default=None, min_length=3, max_length=120)

    @model_validator(mode="after")
    def validate_storage_reference(self):
        if not self.ipfs_cid and not self.storage_uri:
            raise ValueError("Either ipfs_cid or storage_uri is required")
        return self


class PlanStorageOut(BaseModel):
    plan_id: int
    storage_backend: str
    ipfs_cid: str | None = None
    storage_uri: str | None = None
    storage_gateway_url: str | None = None
    preview_url: str | None = None


class TokenizedPropertyCreate(BaseModel):
    location_id: int
    asset_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    issuer_name: str = Field(..., min_length=1, max_length=150)
    issuer_wallet: str = Field(..., min_length=3, max_length=120)
    property_type: str | None = Field(default=None, max_length=80)
    asset_ref: str | None = Field(default=None, max_length=120)
    fractional_enabled: bool = False
    total_units: int = Field(default=1, ge=1, le=1_000_000)
    valuation_amount: float | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=1, max_length=20)
    chain: str | None = Field(default=DEFAULT_CHAIN, min_length=1, max_length=50)
    contract_address: str | None = Field(default=None, min_length=6, max_length=255)
    token_symbol: str | None = Field(default=None, min_length=1, max_length=20)
    token_standard: str | None = Field(default=None, min_length=1, max_length=50)
    tokenization_tx_hash: str | None = None
    asset_metadata: dict = Field(default_factory=dict)
    rights_metadata: dict = Field(default_factory=dict)
    status: str = Field(default="active", min_length=1, max_length=50)

    @field_validator("chain")
    @classmethod
    def validate_chain(cls, value: str | None) -> str | None:
        return _validate_supported_chain(value)

    @model_validator(mode="after")
    def validate_fractional_configuration(self):
        if not self.fractional_enabled and self.total_units != 1:
            raise ValueError("Non-fractional properties must use exactly 1 unit")
        return self


class TokenizedPropertyOut(BaseModel):
    id: int
    location_id: int
    asset_name: str
    description: str | None = None
    issuer_name: str
    issuer_wallet: str
    property_type: str | None = None
    asset_ref: str | None = None
    fractional_enabled: bool
    total_units: int
    valuation_amount: float | None = None
    currency: str
    status: str
    chain: str | None = None
    contract_address: str | None = None
    token_symbol: str | None = None
    token_standard: str | None = None
    tokenization_tx_hash: str | None = None
    tokenized_at: datetime
    asset_metadata: dict = Field(default_factory=dict)
    rights_metadata: dict = Field(default_factory=dict)


class PropertyTokenAllocationOut(BaseModel):
    id: int
    property_id: int
    wallet: str
    holder_name: str | None = None
    units_owned: int
    ownership_pct: float
    status: str


class PropertyUnitTransferRequest(BaseModel):
    transferred_by_wallet: str = Field(..., min_length=3, max_length=120)
    to_wallet: str = Field(..., min_length=3, max_length=120)
    to_holder_name: str | None = Field(default=None, max_length=150)
    units: int = Field(..., ge=1, le=1_000_000)
    consideration_amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=20)
    tx_hash: str | None = None


class PropertyUnitTransferResponse(BaseModel):
    property_id: int
    from_wallet: str
    to_wallet: str
    units_transferred: int
    ownership_pct_transferred: float
    sender_remaining_units: int
    recipient_total_units: int


class PropertyLedgerEventOut(BaseModel):
    id: int
    property_id: int
    event_type: str
    actor_wallet: str | None = None
    from_wallet: str | None = None
    to_wallet: str | None = None
    tx_hash: str | None = None
    chain: str | None = None
    units: int | None = None
    consideration_amount: float | None = None
    currency: str | None = None
    event_metadata: dict = Field(default_factory=dict)


# AI

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    location_id: int | None = None
    compare_ids: list[int] = Field(default_factory=list, max_length=3)


class QueryResponse(BaseModel):
    question: str
    answer: str
    context_label: str | None = None


class AIInsightCard(BaseModel):
    label: str
    value: str
    tone: Literal["strong", "watch", "risk", "neutral"] = "neutral"


class AnalysisResponse(BaseModel):
    location_id: int
    analysis: str
    cards: list[AIInsightCard] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)


class MarketOpportunityOut(BaseModel):
    location_id: int | None = None
    location_name: str
    title: str
    reason: str
    score: float | None = None


class MarketBriefResponse(BaseModel):
    summary: str
    national_thesis: str
    top_opportunities: list[MarketOpportunityOut] = Field(default_factory=list)
    watchouts: list[str] = Field(default_factory=list)
    prompt_suggestions: list[str] = Field(default_factory=list)


class AICompareRequest(BaseModel):
    location_ids: list[int] = Field(..., min_length=2, max_length=3)


class AICompareResponse(BaseModel):
    summary: str
    winner_location_id: int | None = None
    winner_location_name: str | None = None
    verdicts: list[AIInsightCard] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)


class AIBrainModuleProfileOut(BaseModel):
    key: str
    title: str
    description: str
    source_system: str
    order: int
    depends_on: list[str] = Field(default_factory=list)


class AIBrainInterfaceOut(BaseModel):
    key: str
    path: str
    method: Literal["GET", "POST"]
    scope: Literal["system", "location", "query", "comparison"]
    description: str


class AIBrainApproachOut(BaseModel):
    objective: str
    approach: str
    interface_chain: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    principles: list[str] = Field(default_factory=list)
    orchestration_flow: list[str] = Field(default_factory=list)
    interfaces: list[AIBrainInterfaceOut] = Field(default_factory=list)
    modules: list[AIBrainModuleProfileOut] = Field(default_factory=list)


class AIBrainArchitectureLayerOut(BaseModel):
    key: str
    title: str
    role: str
    components: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)


class AIBrainArchitectureOut(BaseModel):
    objective: str
    style: str
    primary_path: list[str] = Field(default_factory=list)
    layers: list[AIBrainArchitectureLayerOut] = Field(default_factory=list)
    request_flow: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    extension_points: list[str] = Field(default_factory=list)
    interfaces: list[AIBrainInterfaceOut] = Field(default_factory=list)


class AILLMProviderOut(BaseModel):
    key: str
    label: str
    model: str
    is_active: bool = False
    supports_text: bool = True
    supports_json: bool = False
    supports_system_instruction: bool = False
    integration_style: str = "native"
    open_source_ready: bool = False
    positioning: str = ""


class AILLMProfileOut(BaseModel):
    abstraction: str
    active_provider: str
    active_model: str
    providers: list[AILLMProviderOut] = Field(default_factory=list)


class AIBrainModuleOut(BaseModel):
    key: str
    title: str
    source_system: str
    summary: str
    status: Literal["ready", "partial", "unavailable"]
    confidence: Literal["high", "medium", "low"]
    signals: list[AIInsightCard] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


class AIBrainRecommendationOut(BaseModel):
    label: str
    action: str
    reason: str
    priority: Literal["high", "medium", "low"]


class AIBrainResponse(BaseModel):
    location_id: int
    location_name: str
    systems_covered: list[str] = Field(default_factory=list)
    thesis: str
    primary_recommendation: str
    modules: list[AIBrainModuleOut] = Field(default_factory=list)
    recommendations: list[AIBrainRecommendationOut] = Field(default_factory=list)


# Common

class ErrorResponse(BaseModel):
    detail: str
