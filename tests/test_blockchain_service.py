from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import brain.blockchain.service as blockchain_service
from brain.blockchain.service import build_plan_token_metadata, calculate_royalty_due, evaluate_usage_rights
from brain.data_bank.models import Location


def make_plan(owner_wallet="0xowner", royalty_bps=750):
    return SimpleNamespace(current_owner_wallet=owner_wallet, royalty_bps=royalty_bps)


def make_license(
    wallet="0xlicensee",
    *,
    personal_use=True,
    commercial_use=False,
    resale_use=False,
    status="active",
    expires_at=None,
    license_id=1,
):
    return SimpleNamespace(
        id=license_id,
        grantee_wallet=wallet,
        personal_use=personal_use,
        commercial_use=commercial_use,
        resale_use=resale_use,
        status=status,
        expires_at=expires_at,
    )


def test_owner_has_full_usage_rights():
    result = evaluate_usage_rights(make_plan(), [], wallet="0xowner", intended_use="resale")

    assert result["allowed"] is True
    assert result["basis"] == "owner"


def test_active_license_allows_requested_use():
    plan = make_plan()
    licenses = [make_license(commercial_use=True)]

    result = evaluate_usage_rights(plan, licenses, wallet="0xlicensee", intended_use="commercial")

    assert result["allowed"] is True
    assert result["basis"] == "license"
    assert result["license_id"] == 1


def test_expired_license_is_not_enforced():
    plan = make_plan()
    licenses = [make_license(expires_at=datetime.now(timezone.utc) - timedelta(days=1))]

    result = evaluate_usage_rights(plan, licenses, wallet="0xlicensee", intended_use="personal")

    assert result["allowed"] is False
    assert result["basis"] == "none"


def test_royalty_is_calculated_in_basis_points():
    assert calculate_royalty_due(1000, 750) == 75.0
    assert calculate_royalty_due(None, 750) == 0.0


def test_build_plan_token_metadata_includes_rights_and_storage():
    plan = SimpleNamespace(
        title="Tower Concept",
        version_label="v2",
        description="Parametric residential tower",
        preview_url="https://cdn.example.com/preview.png",
        storage_uri="ipfs://bafy-plan",
        ipfs_cid="bafy-plan",
        author_name="Architect A",
        license_code="commercial",
        royalty_bps=750,
        location_id=4,
        commercial_license_allowed=True,
        resale_license_allowed=False,
        file_hash="hash-1234",
        rights_metadata={"personal": True},
        constraint_snapshot={"fsi": 2.5},
        zoning_snapshot={"zoning_type": "mixed"},
        massing_inputs={"height_m": 36},
    )

    metadata = build_plan_token_metadata(plan)

    assert metadata["name"] == "Tower Concept #v2"
    assert metadata["external_url"] == "ipfs://bafy-plan"
    assert metadata["properties"]["ipfs_cid"] == "bafy-plan"
    assert any(item["trait_type"] == "license_code" for item in metadata["attributes"])


class DummySession:
    def __init__(self, *, objects=None):
        self.added = []
        self.objects = objects or {}
        self._next_id = 1

    def add(self, value):
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                setattr(value, "id", self._next_id)
                self._next_id += 1
        return None

    def get(self, model, object_id):
        return self.objects.get((model, object_id))


def test_accept_exchange_offer_sale_path(monkeypatch):
    session = DummySession()
    listing = SimpleNamespace(id=2, plan_id=5, seller_wallet="0xseller", listing_type="sale", status="active")
    offer = SimpleNamespace(id=7, listing_id=2, bidder_wallet="0xbuyer", offer_price=1500, currency="USD", intended_use="personal", status="pending", accepted_at=None)

    monkeypatch.setattr(blockchain_service, "get_exchange_offer", lambda _session, _offer_id: offer)
    monkeypatch.setattr(blockchain_service, "get_exchange_listing", lambda _session, _listing_id: listing)
    monkeypatch.setattr(blockchain_service, "list_exchange_offers", lambda _session, _listing_id: [offer])
    monkeypatch.setattr(
        blockchain_service,
        "transfer_plan",
        lambda _session, _plan_id, payload: {"plan": SimpleNamespace(current_owner_wallet=payload["to_wallet"]), "royalty_due": 112.5},
    )

    result = blockchain_service.accept_exchange_offer(session, 7, accepted_by_wallet="0xseller", tx_hash="0xtx")

    assert result["mode"] == "sale"
    assert result["royalty_due"] == 112.5
    assert result["new_owner_wallet"] == "0xbuyer"
    assert listing.status == "settled"
    assert offer.status == "accepted"


def test_accept_exchange_offer_license_path(monkeypatch):
    session = DummySession()
    listing = SimpleNamespace(
        id=3,
        plan_id=9,
        seller_wallet="0xseller",
        listing_type="license",
        status="active",
        personal_use=True,
        commercial_use=True,
        resale_use=False,
        can_sublicense=False,
    )
    offer = SimpleNamespace(id=8, listing_id=3, bidder_wallet="0xbuyer", bidder_name="Buyer", offer_price=500, currency="USD", intended_use="commercial", status="pending", accepted_at=None)

    monkeypatch.setattr(blockchain_service, "get_exchange_offer", lambda _session, _offer_id: offer)
    monkeypatch.setattr(blockchain_service, "get_exchange_listing", lambda _session, _listing_id: listing)
    monkeypatch.setattr(blockchain_service, "list_exchange_offers", lambda _session, _listing_id: [offer])
    monkeypatch.setattr(blockchain_service, "issue_license", lambda _session, _plan_id, payload: SimpleNamespace(id=21, **payload))

    result = blockchain_service.accept_exchange_offer(session, 8, accepted_by_wallet="0xseller")

    assert result["mode"] == "license"
    assert result["license_id"] == 21
    assert result["royalty_due"] == 0.0
    assert result["new_owner_wallet"] is None
    assert listing.status == "settled"
    assert offer.status == "accepted"


def test_tokenize_property_creates_initial_full_allocation():
    session = DummySession(objects={(Location, 3): SimpleNamespace(id=3)})

    property_row = blockchain_service.tokenize_property(session, {
        "location_id": 3,
        "asset_name": "MG Road Trophy Asset",
        "issuer_name": "BuiltAttic SPV",
        "issuer_wallet": "0xissuer",
        "fractional_enabled": True,
        "total_units": 1000,
        "valuation_amount": 2500000,
        "currency": "USD",
        "token_symbol": "MGR",
    })

    allocations = [item for item in session.added if item.__class__.__name__ == "PropertyTokenAllocation"]
    ledger_events = [item for item in session.added if item.__class__.__name__ == "PropertyLedgerEvent"]

    assert property_row.id is not None
    assert property_row.total_units == 1000
    assert property_row.chain == "polygon"
    assert allocations[0].wallet == "0xissuer"
    assert allocations[0].units_owned == 1000
    assert ledger_events[0].event_type == "property_tokenized"
    assert ledger_events[0].units == 1000


def test_transfer_property_units_updates_sender_and_recipient(monkeypatch):
    session = DummySession()
    property_row = SimpleNamespace(id=11, total_units=1000, fractional_enabled=True, status="active", currency="USD", chain="polygon")
    sender_allocation = SimpleNamespace(property_id=11, wallet="0xissuer", holder_name="Issuer", units_owned=1000, status="active")

    monkeypatch.setattr(blockchain_service, "get_tokenized_property", lambda _session, _property_id: property_row)
    monkeypatch.setattr(
        blockchain_service,
        "_get_property_allocation",
        lambda _session, _property_id, wallet: sender_allocation if wallet == "0xissuer" else None,
    )

    result = blockchain_service.transfer_property_units(session, 11, {
        "transferred_by_wallet": "0xissuer",
        "to_wallet": "0xinvestr",
        "to_holder_name": "Investor One",
        "units": 250,
        "consideration_amount": 50000,
        "currency": "USD",
    })

    ledger_events = [item for item in session.added if item.__class__.__name__ == "PropertyLedgerEvent"]

    assert sender_allocation.units_owned == 750
    assert result["recipient_allocation"].wallet == "0xinvestr"
    assert result["recipient_allocation"].units_owned == 250
    assert result["ownership_pct_transferred"] == 25.0
    assert ledger_events[0].event_type == "property_units_transferred"


def test_transfer_property_units_rejects_partial_transfer_for_whole_asset(monkeypatch):
    session = DummySession()
    property_row = SimpleNamespace(id=12, total_units=1, fractional_enabled=False, status="active", currency="USD", chain=None)

    monkeypatch.setattr(blockchain_service, "get_tokenized_property", lambda _session, _property_id: property_row)

    with pytest.raises(ValueError, match="Whole-property tokens must transfer the full unit supply"):
        blockchain_service.transfer_property_units(session, 12, {
            "transferred_by_wallet": "0xowner",
            "to_wallet": "0xbuyer",
            "units": 2,
        })


def test_normalize_chain_rejects_unsupported_value():
    with pytest.raises(ValueError, match="Unsupported chain"):
        blockchain_service.normalize_chain("solana")


def test_list_supported_chains_marks_polygon_default():
    chains = blockchain_service.list_supported_chains()

    assert chains[0]["key"] == "polygon"
    assert chains[0]["is_default"] is True
    assert any(item["key"] == "base" for item in chains)


def test_contract_profile_stays_minimal_and_non_upgradable():
    profile = blockchain_service.get_contract_profile()

    assert profile["philosophy"] == "minimal_auditable"
    assert "no_upgradeability" in profile["principles"]
    assert len(profile["templates"]) == 2
    assert all(template["upgradable"] is False for template in profile["templates"])
    assert any(template["key"] == "plan_registry" for template in profile["templates"])
    assert any(template["key"] == "property_fractional" for template in profile["templates"])


def test_contract_template_source_files_exist():
    profile = blockchain_service.get_contract_profile()

    for template in profile["templates"]:
        assert Path(template["source_path"]).exists()


def test_create_plan_normalizes_ipfs_storage():
    session = DummySession()

    plan = blockchain_service.create_plan(session, {
        "title": "Tower A Plan Set",
        "author_name": "Architect A",
        "author_wallet": "0xauthor",
        "file_hash": "hash-abcdef12",
        "ipfs_cid": "bafybeigdyrzt4examplecid",
    })

    assert plan.ipfs_cid == "bafybeigdyrzt4examplecid"
    assert plan.storage_uri == "ipfs://bafybeigdyrzt4examplecid"


def test_attach_plan_ipfs_storage_updates_metadata(monkeypatch):
    session = DummySession()
    plan = SimpleNamespace(
        id=21,
        title="Tower A Plan Set",
        description="Full drawing pack",
        author_name="Architect A",
        author_wallet="0xauthor",
        current_owner_wallet="0xauthor",
        version_label="v1",
        file_hash="hash-abcdef12",
        preview_url=None,
        storage_uri=None,
        ipfs_cid=None,
        license_code="custom",
        asset_status="minted",
        royalty_bps=500,
        location_id=3,
        commercial_license_allowed=False,
        resale_license_allowed=False,
        rights_metadata={},
        constraint_snapshot={},
        zoning_snapshot={},
        massing_inputs={},
        minted_at=datetime.now(timezone.utc),
        mint_metadata={},
    )
    monkeypatch.setattr(blockchain_service, "get_plan", lambda _session, _plan_id: plan)

    updated_plan = blockchain_service.attach_plan_ipfs_storage(session, 21, {
        "storage_uri": "ipfs://bafybeifilecid123/drawings/floor-plan.pdf",
        "attached_by_wallet": "0xauthor",
    })

    ledger_events = [item for item in session.added if item.__class__.__name__ == "PlanLedgerEvent"]

    assert updated_plan.ipfs_cid == "bafybeifilecid123"
    assert updated_plan.storage_uri == "ipfs://bafybeifilecid123/drawings/floor-plan.pdf"
    assert updated_plan.mint_metadata["properties"]["ipfs_cid"] == "bafybeifilecid123"
    assert updated_plan.mint_metadata["external_url"].endswith("/bafybeifilecid123/drawings/floor-plan.pdf")
    assert ledger_events[0].event_type == "storage_attached"


def test_normalize_plan_storage_rejects_conflicting_non_ipfs_uri():
    with pytest.raises(ValueError, match="storage_uri must be an IPFS URI or gateway URL"):
        blockchain_service.normalize_plan_storage("https://cdn.example.com/file.pdf", "bafybeigdyrzt4examplecid")
