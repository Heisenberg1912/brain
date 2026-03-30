"""Data ingestion pipeline: ingest → normalize → validate → store."""
from brain.data_bank.ingestion.base import BaseIngestor, IngestResult
from brain.data_bank.ingestion.csv_ingestor import CSVIngestor, ingest_directory
from brain.data_bank.ingestion.gemini_web_ingestor import GeminiWebIngestor
from brain.data_bank.ingestion.normalizer import normalize_record, validate_record
from brain.data_bank.ingestion.opencity_ingestor import OpenCityIngestor

__all__ = [
    "BaseIngestor",
    "IngestResult",
    "CSVIngestor",
    "GeminiWebIngestor",
    "OpenCityIngestor",
    "ingest_directory",
    "normalize_record",
    "validate_record",
]
