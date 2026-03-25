from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    ArchitecturalPlanCreate,
    ArchitecturalPlanOut,
    PlanLicenseCreate,
    PlanLicenseOut,
    MintPlanRequest,
    PlanTransferRequest,
    PlanTransferResponse,
    ExchangeListingCreate,
    ExchangeListingOut,
    ExchangeOfferCreate,
    ExchangeOfferOut,
    AcceptExchangeOfferRequest,
    AcceptExchangeOfferResponse,
    CancelExchangeListingRequest,
    PlanLedgerEventOut,
    PropertyLedgerEventOut,
    PropertyTokenAllocationOut,
    PropertyUnitTransferRequest,
    PropertyUnitTransferResponse,
    ContractProfileOut,
    PlanStorageAttachRequest,
    PlanStorageOut,
    SupportedChainOut,
    StorageProfileOut,
    TokenizedPropertyCreate,
    TokenizedPropertyOut,
    TokenMetadataOut,
    UsageRightsCheckRequest,
    UsageRightsCheckResponse,
    ErrorResponse,
)
from brain.blockchain import service as chain_svc

router = APIRouter()


def _plan_to_dict(plan) -> dict:
    storage = chain_svc.get_plan_storage(plan)
    return {
        "id": plan.id,
        "location_id": plan.location_id,
        "title": plan.title,
        "description": plan.description,
        "author_name": plan.author_name,
        "author_wallet": plan.author_wallet,
        "current_owner_wallet": plan.current_owner_wallet,
        "version_label": plan.version_label,
        "file_hash": plan.file_hash,
        "preview_url": plan.preview_url,
        "storage_uri": storage["storage_uri"],
        "ipfs_cid": storage["ipfs_cid"],
        "storage_backend": storage["storage_backend"],
        "storage_gateway_url": storage["storage_gateway_url"],
        "license_code": plan.license_code,
        "asset_status": plan.asset_status,
        "personal_license_allowed": plan.personal_license_allowed,
        "commercial_license_allowed": plan.commercial_license_allowed,
        "resale_license_allowed": plan.resale_license_allowed,
        "royalty_bps": plan.royalty_bps,
        "chain": plan.chain,
        "contract_address": plan.contract_address,
        "token_id": plan.token_id,
        "mint_tx_hash": plan.mint_tx_hash,
        "rights_metadata": plan.rights_metadata or {},
        "constraint_snapshot": plan.constraint_snapshot or {},
        "zoning_snapshot": plan.zoning_snapshot or {},
        "location_intelligence_score": float(plan.location_intelligence_score) if plan.location_intelligence_score is not None else None,
        "massing_inputs": plan.massing_inputs or {},
        "mint_metadata": plan.mint_metadata or {},
    }


def _license_to_dict(license_row) -> dict:
    return {
        "id": license_row.id,
        "plan_id": license_row.plan_id,
        "grantee_wallet": license_row.grantee_wallet,
        "grantee_name": license_row.grantee_name,
        "personal_use": license_row.personal_use,
        "commercial_use": license_row.commercial_use,
        "resale_use": license_row.resale_use,
        "can_sublicense": license_row.can_sublicense,
        "status": license_row.status,
        "note": license_row.note,
        "expires_at": license_row.expires_at,
    }


def _ledger_to_dict(event) -> dict:
    return {
        "id": event.id,
        "plan_id": event.plan_id,
        "event_type": event.event_type,
        "actor_wallet": event.actor_wallet,
        "from_wallet": event.from_wallet,
        "to_wallet": event.to_wallet,
        "tx_hash": event.tx_hash,
        "chain": event.chain,
        "sale_price": float(event.sale_price) if event.sale_price is not None else None,
        "currency": event.currency,
        "event_metadata": event.event_metadata or {},
    }


def _listing_to_dict(listing) -> dict:
    return {
        "id": listing.id,
        "plan_id": listing.plan_id,
        "seller_wallet": listing.seller_wallet,
        "listing_type": listing.listing_type,
        "asking_price": float(listing.asking_price),
        "currency": listing.currency,
        "status": listing.status,
        "personal_use": listing.personal_use,
        "commercial_use": listing.commercial_use,
        "resale_use": listing.resale_use,
        "can_sublicense": listing.can_sublicense,
        "note": listing.note,
        "expires_at": listing.expires_at,
    }


def _offer_to_dict(offer) -> dict:
    return {
        "id": offer.id,
        "listing_id": offer.listing_id,
        "bidder_wallet": offer.bidder_wallet,
        "bidder_name": offer.bidder_name,
        "offer_price": float(offer.offer_price),
        "currency": offer.currency,
        "intended_use": offer.intended_use,
        "status": offer.status,
        "note": offer.note,
    }


def _tokenized_property_to_dict(property_row) -> dict:
    return {
        "id": property_row.id,
        "location_id": property_row.location_id,
        "asset_name": property_row.asset_name,
        "description": property_row.description,
        "issuer_name": property_row.issuer_name,
        "issuer_wallet": property_row.issuer_wallet,
        "property_type": property_row.property_type,
        "asset_ref": property_row.asset_ref,
        "fractional_enabled": property_row.fractional_enabled,
        "total_units": property_row.total_units,
        "valuation_amount": float(property_row.valuation_amount) if property_row.valuation_amount is not None else None,
        "currency": property_row.currency,
        "status": property_row.status,
        "chain": property_row.chain,
        "contract_address": property_row.contract_address,
        "token_symbol": property_row.token_symbol,
        "token_standard": property_row.token_standard,
        "tokenization_tx_hash": property_row.tokenization_tx_hash,
        "tokenized_at": property_row.tokenized_at,
        "asset_metadata": property_row.asset_metadata or {},
        "rights_metadata": property_row.rights_metadata or {},
    }


def _property_allocation_to_dict(allocation, total_units: int) -> dict:
    return {
        "id": allocation.id,
        "property_id": allocation.property_id,
        "wallet": allocation.wallet,
        "holder_name": allocation.holder_name,
        "units_owned": allocation.units_owned,
        "ownership_pct": chain_svc.calculate_ownership_pct(allocation.units_owned, total_units),
        "status": allocation.status,
    }


def _property_ledger_to_dict(event) -> dict:
    return {
        "id": event.id,
        "property_id": event.property_id,
        "event_type": event.event_type,
        "actor_wallet": event.actor_wallet,
        "from_wallet": event.from_wallet,
        "to_wallet": event.to_wallet,
        "tx_hash": event.tx_hash,
        "chain": event.chain,
        "units": event.units,
        "consideration_amount": float(event.consideration_amount) if event.consideration_amount is not None else None,
        "currency": event.currency,
        "event_metadata": event.event_metadata or {},
    }


@router.get("/storage/profile", response_model=StorageProfileOut)
def get_storage_profile():
    return chain_svc.get_storage_profile()


@router.get("/contracts/profile", response_model=ContractProfileOut)
def get_contract_profile():
    return chain_svc.get_contract_profile()


@router.get("/plans", response_model=list[ArchitecturalPlanOut])
def list_plans(
    owner_wallet: str | None = Query(default=None),
    location_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return [_plan_to_dict(plan) for plan in chain_svc.list_plans(db, owner_wallet=owner_wallet, location_id=location_id)]


@router.get("/networks", response_model=list[SupportedChainOut])
def list_supported_networks():
    return chain_svc.list_supported_chains()


@router.get("/properties", response_model=list[TokenizedPropertyOut])
def list_tokenized_properties(
    location_id: int | None = Query(default=None),
    owner_wallet: str | None = Query(default=None),
    fractional_enabled: bool | None = Query(default=None),
    status: str | None = Query(default="active"),
    db: Session = Depends(get_db),
):
    properties = chain_svc.list_tokenized_properties(
        db,
        location_id=location_id,
        owner_wallet=owner_wallet,
        fractional_enabled=fractional_enabled,
        status=status,
    )
    return [_tokenized_property_to_dict(property_row) for property_row in properties]


@router.post(
    "/properties/tokenize",
    response_model=TokenizedPropertyOut,
    responses={404: {"model": ErrorResponse}},
)
def tokenize_property(body: TokenizedPropertyCreate, db: Session = Depends(get_db)):
    try:
        property_row = chain_svc.tokenize_property(db, body.model_dump())
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return _tokenized_property_to_dict(property_row)


@router.get(
    "/properties/{property_id}",
    response_model=TokenizedPropertyOut,
    responses={404: {"model": ErrorResponse}},
)
def get_tokenized_property(property_id: int, db: Session = Depends(get_db)):
    property_row = chain_svc.get_tokenized_property(db, property_id)
    if not property_row:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    return _tokenized_property_to_dict(property_row)


@router.get(
    "/properties/{property_id}/owners",
    response_model=list[PropertyTokenAllocationOut],
    responses={404: {"model": ErrorResponse}},
)
def list_property_allocations(property_id: int, db: Session = Depends(get_db)):
    property_row = chain_svc.get_tokenized_property(db, property_id)
    if not property_row:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    allocations = chain_svc.list_property_allocations(db, property_id)
    return [_property_allocation_to_dict(allocation, property_row.total_units) for allocation in allocations]


@router.post(
    "/properties/{property_id}/transfer",
    response_model=PropertyUnitTransferResponse,
    responses={404: {"model": ErrorResponse}},
)
def transfer_property_units(property_id: int, body: PropertyUnitTransferRequest, db: Session = Depends(get_db)):
    try:
        result = chain_svc.transfer_property_units(db, property_id, body.model_dump())
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return {
        "property_id": result["property"].id,
        "from_wallet": body.transferred_by_wallet,
        "to_wallet": body.to_wallet,
        "units_transferred": result["units_transferred"],
        "ownership_pct_transferred": result["ownership_pct_transferred"],
        "sender_remaining_units": result["sender_allocation"].units_owned,
        "recipient_total_units": result["recipient_allocation"].units_owned,
    }


@router.get(
    "/properties/{property_id}/ledger",
    response_model=list[PropertyLedgerEventOut],
    responses={404: {"model": ErrorResponse}},
)
def get_property_ledger(property_id: int, db: Session = Depends(get_db)):
    property_row = chain_svc.get_tokenized_property(db, property_id)
    if not property_row:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    return [_property_ledger_to_dict(event) for event in chain_svc.get_property_ledger(db, property_id)]


@router.get("/exchange/listings", response_model=list[ExchangeListingOut])
def list_exchange_listings(
    status: str | None = Query(default="active"),
    listing_type: str | None = Query(default=None),
    seller_wallet: str | None = Query(default=None),
    plan_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    listings = chain_svc.list_exchange_listings(
        db,
        status=status,
        listing_type=listing_type,
        seller_wallet=seller_wallet,
        plan_id=plan_id,
    )
    return [_listing_to_dict(listing) for listing in listings]


@router.post(
    "/exchange/listings",
    response_model=ExchangeListingOut,
    responses={404: {"model": ErrorResponse}},
)
def create_exchange_listing(body: ExchangeListingCreate, db: Session = Depends(get_db)):
    try:
        listing = chain_svc.create_exchange_listing(db, body.model_dump())
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return _listing_to_dict(listing)


@router.get(
    "/exchange/listings/{listing_id}",
    response_model=ExchangeListingOut,
    responses={404: {"model": ErrorResponse}},
)
def get_exchange_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = chain_svc.get_exchange_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")
    return _listing_to_dict(listing)


@router.post(
    "/exchange/listings/{listing_id}/cancel",
    response_model=ExchangeListingOut,
    responses={404: {"model": ErrorResponse}},
)
def cancel_exchange_listing(listing_id: int, body: CancelExchangeListingRequest, db: Session = Depends(get_db)):
    try:
        listing = chain_svc.cancel_exchange_listing(db, listing_id, body.cancelled_by_wallet)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return _listing_to_dict(listing)


@router.get("/exchange/listings/{listing_id}/offers", response_model=list[ExchangeOfferOut])
def list_exchange_offers(listing_id: int, db: Session = Depends(get_db)):
    return [_offer_to_dict(offer) for offer in chain_svc.list_exchange_offers(db, listing_id)]


@router.post(
    "/exchange/listings/{listing_id}/offers",
    response_model=ExchangeOfferOut,
    responses={404: {"model": ErrorResponse}},
)
def create_exchange_offer(listing_id: int, body: ExchangeOfferCreate, db: Session = Depends(get_db)):
    try:
        offer = chain_svc.create_exchange_offer(db, listing_id, body.model_dump())
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return _offer_to_dict(offer)


@router.post(
    "/exchange/offers/{offer_id}/accept",
    response_model=AcceptExchangeOfferResponse,
    responses={404: {"model": ErrorResponse}},
)
def accept_exchange_offer(offer_id: int, body: AcceptExchangeOfferRequest, db: Session = Depends(get_db)):
    try:
        result = chain_svc.accept_exchange_offer(
            db,
            offer_id,
            accepted_by_wallet=body.accepted_by_wallet,
            tx_hash=body.tx_hash,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return {
        "listing_id": result["listing"].id,
        "offer_id": result["offer"].id,
        "mode": result["mode"],
        "royalty_due": result["royalty_due"],
        "license_id": result["license_id"],
        "new_owner_wallet": result["new_owner_wallet"],
    }


@router.post(
    "/plans",
    response_model=ArchitecturalPlanOut,
    responses={404: {"model": ErrorResponse}},
)
def create_plan(body: ArchitecturalPlanCreate, db: Session = Depends(get_db)):
    try:
        plan = chain_svc.create_plan(db, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return _plan_to_dict(plan)


@router.get(
    "/plans/{plan_id}",
    response_model=ArchitecturalPlanOut,
    responses={404: {"model": ErrorResponse}},
)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = chain_svc.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return _plan_to_dict(plan)


@router.get(
    "/plans/{plan_id}/storage",
    response_model=PlanStorageOut,
    responses={404: {"model": ErrorResponse}},
)
def get_plan_storage(plan_id: int, db: Session = Depends(get_db)):
    plan = chain_svc.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return chain_svc.get_plan_storage(plan)


@router.post(
    "/plans/{plan_id}/storage/ipfs",
    response_model=PlanStorageOut,
    responses={404: {"model": ErrorResponse}},
)
def attach_plan_ipfs_storage(plan_id: int, body: PlanStorageAttachRequest, db: Session = Depends(get_db)):
    try:
        plan = chain_svc.attach_plan_ipfs_storage(db, plan_id, body.model_dump())
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return chain_svc.get_plan_storage(plan)


@router.get(
    "/plans/{plan_id}/token-metadata",
    response_model=TokenMetadataOut,
    responses={404: {"model": ErrorResponse}},
)
def get_plan_token_metadata(plan_id: int, db: Session = Depends(get_db)):
    plan = chain_svc.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    return chain_svc.build_plan_token_metadata(plan)


@router.post(
    "/plans/{plan_id}/licenses",
    response_model=PlanLicenseOut,
    responses={404: {"model": ErrorResponse}},
)
def issue_license(plan_id: int, body: PlanLicenseCreate, db: Session = Depends(get_db)):
    try:
        license_row = chain_svc.issue_license(db, plan_id, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return _license_to_dict(license_row)


@router.get("/plans/{plan_id}/licenses", response_model=list[PlanLicenseOut])
def list_licenses(plan_id: int, db: Session = Depends(get_db)):
    return [_license_to_dict(item) for item in chain_svc.get_plan_licenses(db, plan_id)]


@router.post(
    "/plans/{plan_id}/mint",
    response_model=ArchitecturalPlanOut,
    responses={404: {"model": ErrorResponse}},
)
def mint_plan(plan_id: int, body: MintPlanRequest, db: Session = Depends(get_db)):
    try:
        plan = chain_svc.record_mint(db, plan_id, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return _plan_to_dict(plan)


@router.post(
    "/plans/{plan_id}/transfer",
    response_model=PlanTransferResponse,
    responses={404: {"model": ErrorResponse}},
)
def transfer_plan(plan_id: int, body: PlanTransferRequest, db: Session = Depends(get_db)):
    try:
        result = chain_svc.transfer_plan(db, plan_id, body.model_dump())
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    db.commit()
    return {
        "plan_id": result["plan"].id,
        "new_owner_wallet": result["plan"].current_owner_wallet,
        "royalty_due": result["royalty_due"],
    }


@router.get("/plans/{plan_id}/ledger", response_model=list[PlanLedgerEventOut])
def get_plan_ledger(plan_id: int, db: Session = Depends(get_db)):
    return [_ledger_to_dict(event) for event in chain_svc.get_plan_ledger(db, plan_id)]


@router.post(
    "/plans/{plan_id}/rights/check",
    response_model=UsageRightsCheckResponse,
    responses={404: {"model": ErrorResponse}},
)
def check_usage_rights(plan_id: int, body: UsageRightsCheckRequest, db: Session = Depends(get_db)):
    plan = chain_svc.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    result = chain_svc.evaluate_usage_rights(
        plan,
        chain_svc.get_plan_licenses(db, plan_id),
        wallet=body.wallet,
        intended_use=body.intended_use,
    )
    return {
        "plan_id": plan_id,
        "wallet": body.wallet,
        "intended_use": body.intended_use,
        **result,
    }
