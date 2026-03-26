from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.blockchain.models import (
    ArchitecturalPlan,
    ExchangeListing,
    ExchangeOffer,
    PlanLedgerEvent,
    PlanLicense,
    PropertyLedgerEvent,
    PropertyTokenAllocation,
    TokenizedProperty,
)
from brain.config import settings
from brain.data_bank.models import Location

USAGE_FIELD_MAP = {
    "personal": "personal_use",
    "commercial": "commercial_use",
    "resale": "resale_use",
}
LISTING_TYPES = {"sale", "license"}
SUPPORTED_CHAINS = {item.strip().lower() for item in settings.supported_plan_chains.split(",") if item.strip()}
DEFAULT_CHAIN = settings.default_plan_chain.strip().lower()
DEFAULT_STORAGE_BACKEND = settings.storage_backend.strip().lower()
IPFS_GATEWAY_BASE = settings.ipfs_gateway_base.rstrip("/")
CHAIN_METADATA = {
    "polygon": {
        "label": "Polygon",
        "supports_fractional": True,
        "supports_plan_nfts": True,
        "positioning": "Lowest-friction default for cheap, mature asset issuance.",
    },
    "base": {
        "label": "Base",
        "supports_fractional": True,
        "supports_plan_nfts": True,
        "positioning": "Simple L2 path with strong Coinbase ecosystem distribution.",
    },
}
IPFS_URI_SCHEME = "ipfs://"
CONTRACT_TEMPLATES = [
    {
        "key": "plan_registry",
        "name": "BuiltAtticPlanRegistry",
        "standard": "ERC-721 + ERC-2981",
        "asset_type": "architectural_plans",
        "upgradable": False,
        "on_chain_scope": ["mint", "ownership", "royalty"],
        "off_chain_scope": ["licensing", "exchange", "compliance", "zoning validation"],
        "source_path": "brain/blockchain/contracts/BuiltAtticPlanRegistry.sol",
    },
    {
        "key": "property_fractional",
        "name": "BuiltAtticProperty1155",
        "standard": "ERC-1155 + ERC-2981",
        "asset_type": "tokenized_properties",
        "upgradable": False,
        "on_chain_scope": ["issue_supply", "ownership", "royalty"],
        "off_chain_scope": ["cap-table policy", "deal execution", "legal verification", "escrow"],
        "source_path": "brain/blockchain/contracts/BuiltAtticProperty1155.sol",
    },
]


def calculate_royalty_due(sale_price: float | Decimal | None, royalty_bps: int) -> float:
    if sale_price is None:
        return 0.0
    return round(float(sale_price) * royalty_bps / 10000, 2)


def get_storage_profile() -> dict[str, str]:
    return {
        "backend": DEFAULT_STORAGE_BACKEND,
        "provider": "ipfs",
        "gateway_base": IPFS_GATEWAY_BASE,
        "uri_scheme": IPFS_URI_SCHEME,
        "upload_mode": "external_pinner",
    }


def get_contract_profile() -> dict[str, Any]:
    return {
        "philosophy": "minimal_auditable",
        "default_network": DEFAULT_CHAIN,
        "storage_backend": DEFAULT_STORAGE_BACKEND,
        "principles": [
            "openzeppelin_primitives_only",
            "no_upgradeability",
            "no_on_chain_exchange",
            "royalties_only_for_economics",
            "metadata_on_ipfs",
        ],
        "templates": CONTRACT_TEMPLATES,
    }


def parse_ipfs_reference(value: str) -> tuple[str, str]:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Invalid IPFS reference")

    if normalized.startswith(IPFS_URI_SCHEME):
        tail = normalized[len(IPFS_URI_SCHEME):]
    elif "/ipfs/" in normalized:
        tail = normalized.split("/ipfs/", 1)[1]
    else:
        tail = normalized

    tail = tail.lstrip("/")
    if not tail:
        raise ValueError("Invalid IPFS reference")

    parts = tail.split("/", 1)
    cid = parts[0].strip()
    path = parts[1].strip("/") if len(parts) > 1 else ""
    if not cid:
        raise ValueError("Invalid IPFS CID")
    return cid, path


def normalize_ipfs_cid(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    cid, _ = parse_ipfs_reference(value)
    return cid


def build_ipfs_uri(cid: str, *, path: str | None = None) -> str:
    suffix = f"/{path.strip('/')}" if path else ""
    return f"{IPFS_URI_SCHEME}{cid}{suffix}"


def build_storage_gateway_url(storage_uri: str | None, ipfs_cid: str | None = None) -> str | None:
    if storage_uri:
        if storage_uri.startswith(IPFS_URI_SCHEME) or "/ipfs/" in storage_uri:
            cid, path = parse_ipfs_reference(storage_uri)
            suffix = f"/{path}" if path else ""
            return f"{IPFS_GATEWAY_BASE}/{cid}{suffix}"
        return storage_uri

    normalized_cid = normalize_ipfs_cid(ipfs_cid)
    if normalized_cid:
        return f"{IPFS_GATEWAY_BASE}/{normalized_cid}"
    return None


def normalize_plan_storage(storage_uri: str | None, ipfs_cid: str | None) -> dict[str, str | None]:
    normalized_uri = storage_uri.strip() if storage_uri else None
    normalized_cid = normalize_ipfs_cid(ipfs_cid)

    if normalized_uri and (normalized_uri.startswith(IPFS_URI_SCHEME) or "/ipfs/" in normalized_uri):
        uri_cid, path = parse_ipfs_reference(normalized_uri)
        if normalized_cid and normalized_cid != uri_cid:
            raise ValueError("storage_uri and ipfs_cid must refer to the same IPFS asset")
        normalized_cid = uri_cid
        normalized_uri = build_ipfs_uri(uri_cid, path=path or None)
    elif normalized_uri and normalized_cid:
        raise ValueError("storage_uri must be an IPFS URI or gateway URL when ipfs_cid is provided")

    if normalized_cid and not normalized_uri:
        normalized_uri = build_ipfs_uri(normalized_cid)

    return {
        "storage_uri": normalized_uri,
        "ipfs_cid": normalized_cid,
        "storage_gateway_url": build_storage_gateway_url(normalized_uri, normalized_cid),
    }


def get_plan_storage(plan: Any) -> dict[str, Any]:
    storage = normalize_plan_storage(getattr(plan, "storage_uri", None), getattr(plan, "ipfs_cid", None))
    storage_uri = storage["storage_uri"]
    is_ipfs_backed = bool(storage["ipfs_cid"]) or bool(storage_uri and (storage_uri.startswith(IPFS_URI_SCHEME) or "/ipfs/" in storage_uri))
    return {
        "plan_id": getattr(plan, "id", None),
        "storage_backend": "ipfs" if is_ipfs_backed else ("external" if storage_uri else DEFAULT_STORAGE_BACKEND),
        "ipfs_cid": storage["ipfs_cid"],
        "storage_uri": storage_uri,
        "storage_gateway_url": storage["storage_gateway_url"],
        "preview_url": getattr(plan, "preview_url", None),
    }


def normalize_chain(chain: str | None, *, fallback_default: bool = False) -> str | None:
    if chain in (None, ""):
        return DEFAULT_CHAIN if fallback_default else None

    normalized = chain.strip().lower()
    if normalized not in SUPPORTED_CHAINS:
        raise ValueError(f"Unsupported chain: {chain}. Supported chains: {', '.join(sorted(SUPPORTED_CHAINS))}")
    return normalized


def list_supported_chains() -> list[dict[str, Any]]:
    chains: list[dict[str, Any]] = []
    for key in sorted(SUPPORTED_CHAINS, key=lambda item: (item != DEFAULT_CHAIN, item)):
        metadata = CHAIN_METADATA.get(key, {})
        chains.append({
            "key": key,
            "label": metadata.get("label", key.title()),
            "is_default": key == DEFAULT_CHAIN,
            "supports_fractional": metadata.get("supports_fractional", True),
            "supports_plan_nfts": metadata.get("supports_plan_nfts", True),
            "positioning": metadata.get("positioning", ""),
        })
    return chains


def calculate_ownership_pct(units: int | None, total_units: int | None) -> float:
    if not units or not total_units:
        return 0.0
    return round((units / total_units) * 100, 4)


def get_plan(session: Session, plan_id: int) -> ArchitecturalPlan | None:
    return session.get(ArchitecturalPlan, plan_id)


def get_tokenized_property(session: Session, property_id: int) -> TokenizedProperty | None:
    return session.get(TokenizedProperty, property_id)


def list_plans(session: Session, owner_wallet: str | None = None, location_id: int | None = None) -> list[ArchitecturalPlan]:
    q = select(ArchitecturalPlan).order_by(ArchitecturalPlan.created_at.desc(), ArchitecturalPlan.id.desc())
    if owner_wallet:
        q = q.where(ArchitecturalPlan.current_owner_wallet == owner_wallet)
    if location_id:
        q = q.where(ArchitecturalPlan.location_id == location_id)
    return list(session.scalars(q))


def list_tokenized_properties(
    session: Session,
    *,
    location_id: int | None = None,
    owner_wallet: str | None = None,
    fractional_enabled: bool | None = None,
    status: str | None = "active",
) -> list[TokenizedProperty]:
    q = select(TokenizedProperty).order_by(TokenizedProperty.created_at.desc(), TokenizedProperty.id.desc())
    if status:
        q = q.where(TokenizedProperty.status == status)
    if location_id:
        q = q.where(TokenizedProperty.location_id == location_id)
    if fractional_enabled is not None:
        q = q.where(TokenizedProperty.fractional_enabled == fractional_enabled)
    if owner_wallet:
        q = (
            q.join(PropertyTokenAllocation)
            .where(PropertyTokenAllocation.wallet == owner_wallet)
            .where(PropertyTokenAllocation.status == "active")
            .where(PropertyTokenAllocation.units_owned > 0)
            .distinct()
        )
    return list(session.scalars(q))


def create_plan(session: Session, payload: dict[str, Any]) -> ArchitecturalPlan:
    location_id = payload.get("location_id")
    if location_id and not session.get(Location, location_id):
        raise ValueError(f"Location {location_id} not found")
    storage = normalize_plan_storage(payload.get("storage_uri"), payload.get("ipfs_cid"))

    plan = ArchitecturalPlan(
        location_id=location_id,
        title=payload["title"],
        description=payload.get("description"),
        author_name=payload["author_name"],
        author_wallet=payload["author_wallet"],
        current_owner_wallet=payload["author_wallet"],
        version_label=payload.get("version_label", "v1"),
        file_hash=payload["file_hash"],
        preview_url=payload.get("preview_url"),
        storage_uri=storage["storage_uri"],
        ipfs_cid=storage["ipfs_cid"],
        license_code=payload.get("license_code", "custom"),
        asset_status=payload.get("asset_status", "draft"),
        personal_license_allowed=payload.get("personal_license_allowed", True),
        commercial_license_allowed=payload.get("commercial_license_allowed", False),
        resale_license_allowed=payload.get("resale_license_allowed", False),
        royalty_bps=payload.get("royalty_bps", 500),
        rights_metadata=payload.get("rights_metadata") or {},
        constraint_snapshot=payload.get("constraint_snapshot") or {},
        zoning_snapshot=payload.get("zoning_snapshot") or {},
        location_intelligence_score=payload.get("location_intelligence_score"),
        massing_inputs=payload.get("massing_inputs") or {},
        mint_metadata=payload.get("mint_metadata") or {},
    )
    session.add(plan)
    session.flush()

    session.add(PlanLedgerEvent(
        plan_id=plan.id,
        event_type="created",
        actor_wallet=plan.author_wallet,
        to_wallet=plan.current_owner_wallet,
        event_metadata={"version_label": plan.version_label},
    ))
    session.flush()
    return plan


def attach_plan_ipfs_storage(session: Session, plan_id: int, payload: dict[str, Any]) -> ArchitecturalPlan:
    plan = get_plan(session, plan_id)
    if not plan:
        raise ValueError(f"Plan {plan_id} not found")

    storage = normalize_plan_storage(payload.get("storage_uri"), payload.get("ipfs_cid"))
    if not storage["ipfs_cid"]:
        raise ValueError("IPFS storage attachment requires a valid IPFS CID or URI")

    plan.storage_uri = storage["storage_uri"]
    plan.ipfs_cid = storage["ipfs_cid"]
    if payload.get("preview_url"):
        plan.preview_url = payload["preview_url"]
    if getattr(plan, "minted_at", None):
        plan.mint_metadata = build_plan_token_metadata(plan)

    session.add(PlanLedgerEvent(
        plan_id=plan.id,
        event_type="storage_attached",
        actor_wallet=payload.get("attached_by_wallet"),
        to_wallet=plan.current_owner_wallet,
        event_metadata={
            "storage_backend": "ipfs",
            "storage_uri": plan.storage_uri,
            "ipfs_cid": plan.ipfs_cid,
            "storage_gateway_url": storage["storage_gateway_url"],
        },
    ))
    session.flush()
    return plan


def _get_property_allocation(session: Session, property_id: int, wallet: str) -> PropertyTokenAllocation | None:
    return session.scalars(
        select(PropertyTokenAllocation)
        .where(PropertyTokenAllocation.property_id == property_id)
        .where(PropertyTokenAllocation.wallet == wallet)
        .order_by(PropertyTokenAllocation.id.desc())
    ).first()


def list_property_allocations(session: Session, property_id: int) -> list[PropertyTokenAllocation]:
    return list(session.scalars(
        select(PropertyTokenAllocation)
        .where(PropertyTokenAllocation.property_id == property_id)
        .where(PropertyTokenAllocation.units_owned > 0)
        .order_by(PropertyTokenAllocation.units_owned.desc(), PropertyTokenAllocation.id.asc())
    ))


def get_property_ledger(session: Session, property_id: int) -> list[PropertyLedgerEvent]:
    return list(session.scalars(
        select(PropertyLedgerEvent)
        .where(PropertyLedgerEvent.property_id == property_id)
        .order_by(PropertyLedgerEvent.created_at.desc(), PropertyLedgerEvent.id.desc())
    ))


def tokenize_property(session: Session, payload: dict[str, Any]) -> TokenizedProperty:
    location_id = payload["location_id"]
    if not session.get(Location, location_id):
        raise ValueError(f"Location {location_id} not found")

    total_units = payload.get("total_units", 1)
    fractional_enabled = payload.get("fractional_enabled", False)
    if not fractional_enabled and total_units != 1:
        raise ValueError("Non-fractional properties must use exactly 1 unit")
    chain = normalize_chain(payload.get("chain"), fallback_default=True)

    property_row = TokenizedProperty(
        location_id=location_id,
        asset_name=payload["asset_name"],
        description=payload.get("description"),
        issuer_name=payload["issuer_name"],
        issuer_wallet=payload["issuer_wallet"],
        property_type=payload.get("property_type"),
        asset_ref=payload.get("asset_ref"),
        fractional_enabled=fractional_enabled,
        total_units=total_units,
        valuation_amount=payload.get("valuation_amount"),
        currency=payload.get("currency", "USD"),
        status=payload.get("status", "active"),
        chain=chain,
        contract_address=payload.get("contract_address"),
        token_symbol=payload.get("token_symbol"),
        token_standard=payload.get("token_standard"),
        tokenization_tx_hash=payload.get("tokenization_tx_hash"),
        asset_metadata=payload.get("asset_metadata") or {},
        rights_metadata=payload.get("rights_metadata") or {},
    )
    session.add(property_row)
    session.flush()

    initial_allocation = PropertyTokenAllocation(
        property_id=property_row.id,
        wallet=property_row.issuer_wallet,
        holder_name=property_row.issuer_name,
        units_owned=property_row.total_units,
        status="active",
    )
    session.add(initial_allocation)

    session.add(PropertyLedgerEvent(
        property_id=property_row.id,
        event_type="property_tokenized",
        actor_wallet=property_row.issuer_wallet,
        to_wallet=property_row.issuer_wallet,
        tx_hash=property_row.tokenization_tx_hash,
        chain=property_row.chain,
        units=property_row.total_units,
        consideration_amount=property_row.valuation_amount,
        currency=property_row.currency,
        event_metadata={
            "fractional_enabled": property_row.fractional_enabled,
            "asset_ref": property_row.asset_ref,
            "token_standard": property_row.token_standard,
        },
    ))
    session.flush()
    return property_row


def transfer_property_units(session: Session, property_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    property_row = get_tokenized_property(session, property_id)
    if not property_row:
        raise ValueError(f"Property {property_id} not found")
    if property_row.status != "active":
        raise ValueError("Only active tokenized properties can be transferred")
    if payload["transferred_by_wallet"] == payload["to_wallet"]:
        raise ValueError("Cannot transfer units to the same wallet")

    units = payload["units"]
    if not property_row.fractional_enabled and units != property_row.total_units:
        raise ValueError("Whole-property tokens must transfer the full unit supply")

    sender_allocation = _get_property_allocation(session, property_id, payload["transferred_by_wallet"])
    if not sender_allocation or sender_allocation.status != "active" or sender_allocation.units_owned < units:
        raise ValueError("Insufficient units for transfer")

    sender_allocation.units_owned -= units
    if sender_allocation.units_owned == 0:
        sender_allocation.status = "transferred"

    recipient_allocation = _get_property_allocation(session, property_id, payload["to_wallet"])
    if recipient_allocation:
        recipient_allocation.units_owned += units
        recipient_allocation.status = "active"
        if payload.get("to_holder_name"):
            recipient_allocation.holder_name = payload["to_holder_name"]
    else:
        recipient_allocation = PropertyTokenAllocation(
            property_id=property_id,
            wallet=payload["to_wallet"],
            holder_name=payload.get("to_holder_name"),
            units_owned=units,
            status="active",
        )
        session.add(recipient_allocation)

    consideration_amount = payload.get("consideration_amount")
    currency = payload.get("currency") or (property_row.currency if consideration_amount is not None else None)
    ownership_pct = calculate_ownership_pct(units, property_row.total_units)

    session.add(PropertyLedgerEvent(
        property_id=property_id,
        event_type="property_units_transferred",
        actor_wallet=payload["transferred_by_wallet"],
        from_wallet=payload["transferred_by_wallet"],
        to_wallet=payload["to_wallet"],
        tx_hash=payload.get("tx_hash"),
        chain=property_row.chain,
        units=units,
        consideration_amount=consideration_amount,
        currency=currency,
        event_metadata={"ownership_pct_transferred": ownership_pct},
    ))
    session.flush()

    return {
        "property": property_row,
        "sender_allocation": sender_allocation,
        "recipient_allocation": recipient_allocation,
        "units_transferred": units,
        "ownership_pct_transferred": ownership_pct,
    }


def issue_license(session: Session, plan_id: int, payload: dict[str, Any]) -> PlanLicense:
    plan = get_plan(session, plan_id)
    if not plan:
        raise ValueError(f"Plan {plan_id} not found")

    license_row = PlanLicense(
        plan_id=plan_id,
        grantee_wallet=payload["grantee_wallet"],
        grantee_name=payload.get("grantee_name"),
        personal_use=payload.get("personal_use", True),
        commercial_use=payload.get("commercial_use", False),
        resale_use=payload.get("resale_use", False),
        can_sublicense=payload.get("can_sublicense", False),
        status=payload.get("status", "active"),
        note=payload.get("note"),
        expires_at=payload.get("expires_at"),
    )
    session.add(license_row)
    session.flush()

    session.add(PlanLedgerEvent(
        plan_id=plan_id,
        event_type="license_issued",
        actor_wallet=plan.current_owner_wallet,
        to_wallet=license_row.grantee_wallet,
        event_metadata={
            "license_id": license_row.id,
            "personal_use": license_row.personal_use,
            "commercial_use": license_row.commercial_use,
            "resale_use": license_row.resale_use,
        },
    ))
    session.flush()
    return license_row


def record_mint(session: Session, plan_id: int, payload: dict[str, Any]) -> ArchitecturalPlan:
    plan = get_plan(session, plan_id)
    if not plan:
        raise ValueError(f"Plan {plan_id} not found")

    plan.chain = normalize_chain(payload["chain"])
    plan.contract_address = payload["contract_address"]
    plan.token_id = payload["token_id"]
    plan.mint_tx_hash = payload.get("tx_hash")
    plan.minted_at = datetime.now(timezone.utc)
    plan.asset_status = "minted"
    plan.mint_metadata = build_plan_token_metadata(plan)

    session.add(PlanLedgerEvent(
        plan_id=plan_id,
        event_type="minted",
        actor_wallet=payload.get("minted_by_wallet") or plan.current_owner_wallet,
        to_wallet=plan.current_owner_wallet,
        tx_hash=plan.mint_tx_hash,
        chain=plan.chain,
        event_metadata={
            "contract_address": plan.contract_address,
            "token_id": plan.token_id,
        },
    ))
    session.flush()
    return plan


def build_plan_token_metadata(plan: ArchitecturalPlan) -> dict[str, Any]:
    storage = get_plan_storage(plan)
    return {
        "name": f"{plan.title} #{plan.version_label}",
        "description": plan.description,
        "image": plan.preview_url,
        "external_url": storage["storage_uri"] or plan.preview_url,
        "attributes": [
            {"trait_type": "author", "value": plan.author_name},
            {"trait_type": "version", "value": plan.version_label},
            {"trait_type": "license_code", "value": plan.license_code},
            {"trait_type": "royalty_bps", "value": plan.royalty_bps},
            {"trait_type": "location_id", "value": plan.location_id},
            {"trait_type": "commercial_use", "value": plan.commercial_license_allowed},
            {"trait_type": "resale_use", "value": plan.resale_license_allowed},
        ],
        "properties": {
            "file_hash": plan.file_hash,
            "storage_backend": storage["storage_backend"],
            "storage_uri": storage["storage_uri"],
            "storage_gateway_url": storage["storage_gateway_url"],
            "ipfs_cid": storage["ipfs_cid"],
            "rights_metadata": plan.rights_metadata or {},
            "constraint_snapshot": plan.constraint_snapshot or {},
            "zoning_snapshot": plan.zoning_snapshot or {},
            "massing_inputs": plan.massing_inputs or {},
        },
    }


def transfer_plan(session: Session, plan_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    plan = get_plan(session, plan_id)
    if not plan:
        raise ValueError(f"Plan {plan_id} not found")
    if payload["transferred_by_wallet"] != plan.current_owner_wallet:
        raise ValueError("Only the current owner can transfer this plan")

    previous_owner = plan.current_owner_wallet
    plan.current_owner_wallet = payload["to_wallet"]
    royalty_due = calculate_royalty_due(payload.get("sale_price"), plan.royalty_bps)

    session.add(PlanLedgerEvent(
        plan_id=plan_id,
        event_type=payload.get("transfer_type", "transfer"),
        actor_wallet=payload["transferred_by_wallet"],
        from_wallet=previous_owner,
        to_wallet=payload["to_wallet"],
        tx_hash=payload.get("tx_hash"),
        chain=plan.chain,
        sale_price=payload.get("sale_price"),
        currency=payload.get("currency"),
        event_metadata={"royalty_due": royalty_due},
    ))
    session.flush()

    return {
        "plan": plan,
        "royalty_due": royalty_due,
    }


def mint_plan(session: Session, plan_id: int, wallet: str) -> ArchitecturalPlan:
    """Mints an architectural plan as an NFT (Mock implementation)."""
    plan = get_plan(session, plan_id)
    if not plan:
        raise ValueError(f"Plan {plan_id} not found")
    if plan.asset_status == "minted":
        raise ValueError("Plan is already minted")
    
    # Mocking on-chain transaction
    tx_hash = f"0xmock_mint_{plan_id}_{datetime.now(timezone.utc).timestamp()}"
    token_id = str(1000 + plan_id)
    
    return record_mint(
        session, 
        plan_id, 
        {
            "chain": DEFAULT_CHAIN,
            "contract_address": "0xBuiltAtticPlanRegistryMockAddress",
            "token_id": token_id,
            "tx_hash": tx_hash,
            "minted_by_wallet": wallet
        }
    )


def tokenize_property_on_chain(session: Session, property_id: int, wallet: str) -> TokenizedProperty:
    """Tokenizes a property on-chain (Mock implementation)."""
    prop = get_tokenized_property(session, property_id)
    if not prop:
        raise ValueError(f"Property {property_id} not found")
    
    # Mocking on-chain transaction
    tx_hash = f"0xmock_tokenize_{property_id}_{datetime.now(timezone.utc).timestamp()}"
    
    prop.status = "active"
    prop.tokenization_tx_hash = tx_hash
    prop.contract_address = "0xBuiltAtticProperty1155MockAddress"
    prop.token_standard = "ERC-1155"
    prop.token_symbol = "BATTIC"
    
    session.add(PropertyLedgerEvent(
        property_id=property_id,
        event_type="on_chain_tokenization",
        actor_wallet=wallet,
        tx_hash=tx_hash,
        chain=prop.chain,
        event_metadata={"status": "active"}
    ))
    session.flush()
    return prop


def get_plan_licenses(session: Session, plan_id: int) -> list[PlanLicense]:
    return list(session.scalars(
        select(PlanLicense)
        .where(PlanLicense.plan_id == plan_id)
        .order_by(PlanLicense.issued_at.desc(), PlanLicense.id.desc())
    ))


def get_plan_ledger(session: Session, plan_id: int) -> list[PlanLedgerEvent]:
    return list(session.scalars(
        select(PlanLedgerEvent)
        .where(PlanLedgerEvent.plan_id == plan_id)
        .order_by(PlanLedgerEvent.created_at.desc(), PlanLedgerEvent.id.desc())
    ))


def get_exchange_listing(session: Session, listing_id: int) -> ExchangeListing | None:
    return session.get(ExchangeListing, listing_id)


def list_exchange_listings(
    session: Session,
    *,
    status: str | None = "active",
    listing_type: str | None = None,
    seller_wallet: str | None = None,
    plan_id: int | None = None,
) -> list[ExchangeListing]:
    q = select(ExchangeListing).order_by(ExchangeListing.created_at.desc(), ExchangeListing.id.desc())
    if status:
        q = q.where(ExchangeListing.status == status)
    if listing_type:
        q = q.where(ExchangeListing.listing_type == listing_type)
    if seller_wallet:
        q = q.where(ExchangeListing.seller_wallet == seller_wallet)
    if plan_id:
        q = q.where(ExchangeListing.plan_id == plan_id)
    return list(session.scalars(q))


def create_exchange_listing(session: Session, payload: dict[str, Any]) -> ExchangeListing:
    plan = get_plan(session, payload["plan_id"])
    if not plan:
        raise ValueError(f"Plan {payload['plan_id']} not found")
    if payload["seller_wallet"] != plan.current_owner_wallet:
        raise ValueError("Only the current owner can create an exchange listing")

    listing_type = payload.get("listing_type", "sale")
    if listing_type not in LISTING_TYPES:
        raise ValueError(f"Unsupported listing type: {listing_type}")

    listing = ExchangeListing(
        plan_id=plan.id,
        seller_wallet=payload["seller_wallet"],
        listing_type=listing_type,
        asking_price=payload["asking_price"],
        currency=payload.get("currency", "USD"),
        status=payload.get("status", "active"),
        personal_use=payload.get("personal_use", True),
        commercial_use=payload.get("commercial_use", False),
        resale_use=payload.get("resale_use", False),
        can_sublicense=payload.get("can_sublicense", False),
        note=payload.get("note"),
        expires_at=payload.get("expires_at"),
    )
    session.add(listing)
    session.flush()

    session.add(PlanLedgerEvent(
        plan_id=plan.id,
        event_type="exchange_listed",
        actor_wallet=listing.seller_wallet,
        event_metadata={
            "listing_id": listing.id,
            "listing_type": listing.listing_type,
            "asking_price": float(listing.asking_price),
            "currency": listing.currency,
        },
    ))
    session.flush()
    return listing


def cancel_exchange_listing(session: Session, listing_id: int, cancelled_by_wallet: str) -> ExchangeListing:
    listing = get_exchange_listing(session, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")
    if listing.seller_wallet != cancelled_by_wallet:
        raise ValueError("Only the seller can cancel this listing")
    if listing.status != "active":
        raise ValueError("Only active listings can be cancelled")

    listing.status = "cancelled"
    session.add(PlanLedgerEvent(
        plan_id=listing.plan_id,
        event_type="exchange_cancelled",
        actor_wallet=cancelled_by_wallet,
        event_metadata={"listing_id": listing.id},
    ))
    session.flush()
    return listing


def get_exchange_offer(session: Session, offer_id: int) -> ExchangeOffer | None:
    return session.get(ExchangeOffer, offer_id)


def list_exchange_offers(session: Session, listing_id: int) -> list[ExchangeOffer]:
    return list(session.scalars(
        select(ExchangeOffer)
        .where(ExchangeOffer.listing_id == listing_id)
        .order_by(ExchangeOffer.created_at.desc(), ExchangeOffer.id.desc())
    ))


def create_exchange_offer(session: Session, listing_id: int, payload: dict[str, Any]) -> ExchangeOffer:
    listing = get_exchange_listing(session, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")
    if listing.status != "active":
        raise ValueError("Offers can only be submitted to active listings")
    if payload.get("currency", listing.currency) != listing.currency:
        raise ValueError("Offer currency must match listing currency")

    offer = ExchangeOffer(
        listing_id=listing_id,
        bidder_wallet=payload["bidder_wallet"],
        bidder_name=payload.get("bidder_name"),
        offer_price=payload["offer_price"],
        currency=payload.get("currency", listing.currency),
        intended_use=payload.get("intended_use", "personal"),
        status=payload.get("status", "pending"),
        note=payload.get("note"),
    )
    session.add(offer)
    session.flush()

    session.add(PlanLedgerEvent(
        plan_id=listing.plan_id,
        event_type="exchange_offer_submitted",
        actor_wallet=offer.bidder_wallet,
        to_wallet=listing.seller_wallet,
        event_metadata={
            "listing_id": listing.id,
            "offer_id": offer.id,
            "offer_price": float(offer.offer_price),
            "currency": offer.currency,
            "intended_use": offer.intended_use,
        },
    ))
    session.flush()
    return offer


def _build_license_payload_from_listing(listing: ExchangeListing, offer: ExchangeOffer) -> dict[str, Any]:
    requested_field = USAGE_FIELD_MAP.get(offer.intended_use)
    if requested_field and not getattr(listing, requested_field, False):
        raise ValueError(f"Listing does not grant {offer.intended_use} rights")

    return {
        "grantee_wallet": offer.bidder_wallet,
        "grantee_name": offer.bidder_name,
        "personal_use": listing.personal_use,
        "commercial_use": listing.commercial_use,
        "resale_use": listing.resale_use,
        "can_sublicense": listing.can_sublicense,
        "status": "active",
        "note": f"Issued from exchange listing #{listing.id}",
    }


def accept_exchange_offer(
    session: Session,
    offer_id: int,
    *,
    accepted_by_wallet: str,
    tx_hash: str | None = None,
) -> dict[str, Any]:
    offer = get_exchange_offer(session, offer_id)
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")

    listing = get_exchange_listing(session, offer.listing_id)
    if not listing:
        raise ValueError(f"Listing {offer.listing_id} not found")
    if listing.seller_wallet != accepted_by_wallet:
        raise ValueError("Only the seller can accept this offer")
    if listing.status != "active":
        raise ValueError("Only active listings can accept offers")
    if offer.status != "pending":
        raise ValueError("Only pending offers can be accepted")

    offer.status = "accepted"
    offer.accepted_at = datetime.now(timezone.utc)
    listing.status = "settled"

    for competing_offer in list_exchange_offers(session, listing.id):
        if competing_offer.id != offer.id and competing_offer.status == "pending":
            competing_offer.status = "rejected"

    settlement: dict[str, Any]
    if listing.listing_type == "sale":
        transfer_result = transfer_plan(
            session,
            listing.plan_id,
            {
                "transferred_by_wallet": accepted_by_wallet,
                "to_wallet": offer.bidder_wallet,
                "transfer_type": "exchange_sale",
                "sale_price": offer.offer_price,
                "currency": offer.currency,
                "tx_hash": tx_hash,
            },
        )
        settlement = {
            "mode": "sale",
            "royalty_due": transfer_result["royalty_due"],
            "license_id": None,
            "new_owner_wallet": transfer_result["plan"].current_owner_wallet,
        }
    else:
        license_row = issue_license(session, listing.plan_id, _build_license_payload_from_listing(listing, offer))
        session.add(PlanLedgerEvent(
            plan_id=listing.plan_id,
            event_type="exchange_license_settled",
            actor_wallet=accepted_by_wallet,
            to_wallet=offer.bidder_wallet,
            tx_hash=tx_hash,
            sale_price=offer.offer_price,
            currency=offer.currency,
            event_metadata={"listing_id": listing.id, "offer_id": offer.id, "license_id": license_row.id},
        ))
        settlement = {
            "mode": "license",
            "royalty_due": 0.0,
            "license_id": license_row.id,
            "new_owner_wallet": None,
        }

    session.add(PlanLedgerEvent(
        plan_id=listing.plan_id,
        event_type="exchange_offer_accepted",
        actor_wallet=accepted_by_wallet,
        to_wallet=offer.bidder_wallet,
        tx_hash=tx_hash,
        sale_price=offer.offer_price,
        currency=offer.currency,
        event_metadata={"listing_id": listing.id, "offer_id": offer.id, "mode": settlement["mode"]},
    ))
    session.flush()
    return {
        "listing": listing,
        "offer": offer,
        **settlement,
    }


def evaluate_usage_rights(plan: Any, licenses: list[Any], wallet: str, intended_use: str) -> dict[str, Any]:
    if intended_use not in USAGE_FIELD_MAP:
        raise ValueError(f"Unsupported usage type: {intended_use}")

    if wallet == plan.current_owner_wallet:
        return {
            "allowed": True,
            "basis": "owner",
            "license_id": None,
            "reason": "Current owner retains full usage rights.",
            "royalty_bps": plan.royalty_bps,
        }

    field_name = USAGE_FIELD_MAP[intended_use]
    now = datetime.now(timezone.utc)
    for license_row in licenses:
        is_active = getattr(license_row, "status", "active") == "active"
        not_expired = getattr(license_row, "expires_at", None) in (None, "") or license_row.expires_at >= now
        matches_wallet = getattr(license_row, "grantee_wallet", None) == wallet
        if is_active and not_expired and matches_wallet and getattr(license_row, field_name, False):
            return {
                "allowed": True,
                "basis": "license",
                "license_id": getattr(license_row, "id", None),
                "reason": f"Active license grants {intended_use} usage.",
                "royalty_bps": plan.royalty_bps,
            }

    return {
        "allowed": False,
        "basis": "none",
        "license_id": None,
        "reason": f"No active license grants {intended_use} usage for this wallet.",
        "royalty_bps": plan.royalty_bps,
    }
