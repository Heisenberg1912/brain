"""Helpers for dataset lineage, raw record storage, and provenance metadata."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROVENANCE_SCHEMA_VERSION = "v1"


def _clean_record(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {}
    return {
        key: value
        for key, value in record.items()
        if not str(key).startswith("__")
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def build_provenance_payload(
    *,
    record_type: str,
    raw_record: dict[str, Any] | None,
    source_path: str,
    row_number: int | None,
    normalized_record: dict[str, Any] | None = None,
    dataset_version: str | None = None,
    pipeline: str = "csv_ingestor",
) -> dict[str, Any]:
    cleaned_raw = _clean_record(raw_record)
    cleaned_normalized = _clean_record(normalized_record)
    normalized_source_path = (
        source_path
        if str(source_path).startswith(("http://", "https://"))
        else Path(source_path).as_posix()
    )
    resolved_dataset_version = (
        dataset_version
        or cleaned_normalized.get("dataset_version")
        or cleaned_raw.get("dataset_version")
        or "seed_v1"
    )
    source_name = cleaned_raw.get("source") or cleaned_normalized.get("source") or Path(source_path).stem
    source_url = cleaned_raw.get("source_url") or cleaned_normalized.get("source_url")

    fingerprint_payload = {
        "record_type": record_type,
        "dataset_version": resolved_dataset_version,
        "normalized_record": cleaned_normalized or cleaned_raw,
    }

    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "pipeline": pipeline,
        "record_type": record_type,
        "dataset_version": resolved_dataset_version,
        "source_file": normalized_source_path,
        "source_name": source_name,
        "source_url": source_url,
        "row_number": row_number,
        "record_hash": _stable_hash(fingerprint_payload),
        "raw_record": cleaned_raw,
        "normalized_record": cleaned_normalized or None,
    }


def assign_raw_data(model: Any, provenance: dict[str, Any]) -> Any:
    if hasattr(model, "raw_data"):
        model.raw_data = {
            "provenance": provenance,
        }
    return model
