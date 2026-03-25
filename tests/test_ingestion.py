"""Tests for the data ingestion pipeline — normalizer and validator."""
import pytest
from brain.data_bank.ingestion.csv_ingestor import CSVIngestor
from brain.data_bank.ingestion.gemini_web_ingestor import (
    GeminiEnrichmentJob,
    GeminiWebIngestor,
    _is_placeholder_url,
    fetch_url_text,
)
from brain.data_bank.ingestion.normalizer import normalize_record, validate_record
from brain.data_bank.ingestion.provenance import build_provenance_payload


class TestNormalizeLocation:
    def test_strips_whitespace(self):
        rec = normalize_record({"name": "  Whitefield  ", "lat": "12.9", "lng": "77.7"}, "location")
        assert rec["name"] == "Whitefield"

    def test_coerces_lat_lng(self):
        rec = normalize_record({"name": "Test", "lat": "12.9716", "lng": "77.5946"}, "location")
        assert isinstance(rec["lat"], float)
        assert isinstance(rec["lng"], float)

    def test_empty_string_becomes_none(self):
        rec = normalize_record({"name": "Test", "pin_code": ""}, "location")
        assert rec["pin_code"] is None


class TestNormalizeZoning:
    def test_lowercases_zoning_type(self):
        rec = normalize_record({"zoning_type": "MIXED", "fsi": "2.5"}, "zoning")
        assert rec["zoning_type"] == "mixed"

    def test_coerces_fsi(self):
        rec = normalize_record({"fsi": "3.0"}, "zoning")
        assert rec["fsi"] == 3.0


class TestNormalizePrice:
    def test_coerces_price(self):
        rec = normalize_record({"price_per_sqft": "5500.50"}, "price")
        assert rec["price_per_sqft"] == 5500.50

    def test_lowercases_property_type(self):
        rec = normalize_record({"property_type": "Apartment"}, "price")
        assert rec["property_type"] == "apartment"


class TestValidateLocation:
    def test_valid_location(self):
        errors = validate_record({"name": "Test", "lat": 12.9, "lng": 77.5}, "location")
        assert errors == []

    def test_missing_name(self):
        errors = validate_record({"lat": 12.9, "lng": 77.5}, "location")
        assert len(errors) == 1
        assert "name" in errors[0].lower()

    def test_invalid_latitude(self):
        errors = validate_record({"name": "Test", "lat": 100.0, "lng": 77.5}, "location")
        assert len(errors) == 1
        assert "latitude" in errors[0].lower()

    def test_invalid_longitude(self):
        errors = validate_record({"name": "Test", "lat": 12.9, "lng": 200.0}, "location")
        assert len(errors) == 1


class TestValidatePrice:
    def test_valid_price(self):
        errors = validate_record({"location_name": "X", "price_per_sqft": 5000, "recorded_date": "2024-01-01"}, "price")
        assert errors == []

    def test_negative_price(self):
        errors = validate_record({"location_name": "X", "price_per_sqft": -100, "recorded_date": "2024-01-01"}, "price")
        assert any("price" in e.lower() for e in errors)

    def test_missing_date(self):
        errors = validate_record({"location_name": "X", "price_per_sqft": 5000}, "price")
        assert any("date" in e.lower() for e in errors)


class TestValidateCensus:
    def test_negative_population(self):
        errors = validate_record({"location_name": "X", "population": -100}, "census")
        assert any("population" in e.lower() for e in errors)


class TestNewDatasets:
    def test_normalize_gis_record(self):
        rec = normalize_record({
            "location_name": "Whitefield",
            "terrain_class": "Gentle",
            "terrain_slope_pct": "4.5",
            "tags": "GIS|Climate",
        }, "gis")
        assert rec["terrain_class"] == "gentle"
        assert rec["terrain_slope_pct"] == 4.5
        assert rec["tags"] == ["gis", "climate"]

    def test_validate_standard_requires_core_fields(self):
        errors = validate_record({"standard_type": "bylaw"}, "standard")
        assert any("code" in error.lower() for error in errors)
        assert any("title" in error.lower() for error in errors)


class TestProvenanceLayer:
    def test_build_provenance_payload_tracks_source_lineage(self):
        payload = build_provenance_payload(
            record_type="price",
            raw_record={"location_name": "Whitefield", "source": "housing.com", "price_per_sqft": "12000"},
            normalized_record={"location_name": "Whitefield", "source": "housing.com", "price_per_sqft": 12000.0},
            source_path="seed_data/prices.csv",
            row_number=14,
            dataset_version="seed_v1",
            pipeline="seed_loader",
        )

        assert payload["record_type"] == "price"
        assert payload["dataset_version"] == "seed_v1"
        assert payload["source_file"].endswith("seed_data/prices.csv")
        assert payload["row_number"] == 14
        assert payload["record_hash"]
        assert payload["source_name"] == "housing.com"
        assert payload["source_file"] == "seed_data/prices.csv"

    def test_csv_ingestor_dedupes_duplicate_price_rows_with_provenance(self, monkeypatch):
        ingestor = CSVIngestor(None, "price", location_map={"Whitefield": 1})
        monkeypatch.setattr(ingestor, "_find_existing", lambda _rec: None)

        raw_rows = [
            {
                "location_name": "Whitefield",
                "price_per_sqft": "12000",
                "property_type": "apartment",
                "recorded_date": "2025-01-01",
                "source": "housing.com",
                "__source_path": "seed_data/prices.csv",
                "__row_number": 2,
            },
            {
                "location_name": "Whitefield",
                "price_per_sqft": "12000",
                "property_type": "apartment",
                "recorded_date": "2025-01-01",
                "source": "housing.com",
                "__source_path": "seed_data/prices.csv",
                "__row_number": 3,
            },
        ]

        models = ingestor.transform(raw_rows)

        assert len(models) == 1
        assert models[0].location_id == 1
        assert models[0].raw_data["provenance"]["source_file"].endswith("seed_data/prices.csv")

    def test_build_provenance_payload_preserves_http_urls(self):
        payload = build_provenance_payload(
            record_type="standard",
            raw_record={"source": "dda"},
            source_path="https://example.gov/dda-bylaws",
            row_number=None,
        )

        assert payload["source_file"] == "https://example.gov/dda-bylaws"


class TestGeminiWebIngestor:
    def test_placeholder_urls_are_detected(self):
        assert _is_placeholder_url("https://example.gov/masterplan")
        assert not _is_placeholder_url("https://dda.gov.in/faqs-building")

    def test_fetch_url_text_strips_html_noise(self, monkeypatch):
        class _FakeResponse:
            def __init__(self, html):
                self._html = html.encode("utf-8")
                self.headers = {"Content-Type": "text/html; charset=utf-8"}

            def read(self):
                return self._html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(
            "brain.data_bank.ingestion.gemini_web_ingestor.urlopen",
            lambda *_args, **_kwargs: _FakeResponse(
                "<html><head><script>bad()</script></head><body><h1>Title</h1><p>Hello World</p></body></html>"
            ),
        )

        text = fetch_url_text("https://example.com")

        assert "Title" in text
        assert "Hello World" in text
        assert "bad()" not in text

    def test_fetch_url_text_can_disable_ssl_verification(self, monkeypatch):
        captured = {}

        class _FakeResponse:
            def __init__(self, html):
                self._html = html.encode("utf-8")
                self.headers = {"Content-Type": "text/html; charset=utf-8"}

            def read(self):
                return self._html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def _fake_urlopen(_request, timeout=None, context=None):
            captured["timeout"] = timeout
            captured["context"] = context
            return _FakeResponse("<html><body><p>Secure Hello</p></body></html>")

        monkeypatch.setattr("brain.data_bank.ingestion.gemini_web_ingestor.urlopen", _fake_urlopen)

        text = fetch_url_text("https://www.hmda.gov.in/planning-2/", verify_ssl=False, timeout=33)

        assert "Secure Hello" in text
        assert captured["timeout"] == 33
        assert captured["context"] is not None

    def test_run_job_reports_placeholder_manifest_urls(self):
        class _FakeSession:
            def scalars(self, *_args, **_kwargs):
                return []

            def commit(self):
                return None

        job = GeminiEnrichmentJob(
            record_type="standard",
            urls=["https://example.gov/bylaw"],
            defaults={"tags": ["official", "gemini"]},
        )
        result = GeminiWebIngestor(_FakeSession()).run_job(job)

        assert result.records_read == 0
        assert result.records_stored == 0
        assert result.errors
        assert "placeholder URL in manifest" in result.errors[0]

    def test_run_job_uses_gemini_output_and_ingests_structured_records(self, monkeypatch):
        class _FakeSession:
            def scalar(self, *_args, **_kwargs):
                return None

            def scalars(self, *_args, **_kwargs):
                return []

            def commit(self):
                return None

        class _FakeAdapter:
            def generate_json(self, *_args, **_kwargs):
                return {
                    "records": [
                        {
                            "standard_type": "bylaw",
                            "country_code": "IN",
                            "admin_area": "Karnataka",
                            "code": "BLR-01",
                            "title": "Building Height Controls",
                            "version_tag": "web_2026_q1",
                        }
                    ]
                }

        monkeypatch.setattr(
            "brain.data_bank.ingestion.gemini_web_ingestor.fetch_url_text",
            lambda _url, **_kwargs: "Official building bylaw page content",
        )
        monkeypatch.setattr(CSVIngestor, "load", lambda self, models: len(models))

        job = GeminiEnrichmentJob(
            record_type="standard",
            urls=["https://dda.gov.in/faqs-building"],
            defaults={"tags": ["official", "gemini"]},
            context="Extract bylaws",
        )
        result = GeminiWebIngestor(_FakeSession(), adapter=_FakeAdapter()).run_job(job)

        assert result.records_read == 1
        assert result.records_stored == 1
        assert result.records_skipped == 0
