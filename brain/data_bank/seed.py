"""Seed loader built on the same provenance-aware ingestion pipeline."""
from __future__ import annotations

from sqlalchemy.orm import Session

from brain.config import SEED_DATA_DIR
from brain.data_bank.ingestion.csv_ingestor import ingest_directory


def seed_all(session: Session):
    results = ingest_directory(
        session,
        str(SEED_DATA_DIR),
        dataset_version_default="seed_v1",
        pipeline_name="seed_loader",
    )

    ordered_labels = [
        ("locations", "locations"),
        ("zoning", "zoning"),
        ("price", "property prices"),
        ("infrastructure", "infrastructure"),
        ("census", "census data"),
        ("gis", "GIS profiles"),
        ("standard", "regional standards"),
    ]
    for key, label in ordered_labels:
        result = results.get(key)
        if not result:
            continue
        print(f"Seeding {label}...")
        print(
            "  -> "
            f"{result.records_stored} stored "
            f"({result.records_read} read, {result.records_skipped} skipped)"
        )

    print("Seed complete.")
