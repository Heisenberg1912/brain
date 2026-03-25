"""Base ingestor interface and shared types."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Summary of an ingestion run."""
    source: str
    records_read: int = 0
    records_stored: int = 0
    records_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.records_read == 0:
            return 0.0
        return self.records_stored / self.records_read * 100


class BaseIngestor(ABC):
    """Abstract base for all data ingestors.

    Subclasses implement extract() and transform(). The base class
    handles the load step and error tracking.
    """

    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def extract(self, source_path: str) -> list[dict]:
        """Read raw records from the source. Returns list of dicts."""
        ...

    @abstractmethod
    def transform(self, raw_records: list[dict]) -> list:
        """Normalize and convert raw dicts into ORM model instances."""
        ...

    def load(self, models: list) -> int:
        """Persist ORM instances to the database. Returns count stored."""
        stored = 0
        for model in models:
            try:
                self.session.add(model)
                self.session.flush()
                stored += 1
            except Exception as e:
                self.session.rollback()
                logger.warning("Failed to store record: %s", e)
        return stored

    def run(self, source_path: str) -> IngestResult:
        """Execute the full ETL pipeline: extract → transform → load."""
        result = IngestResult(source=source_path)

        # Extract
        raw = self.extract(source_path)
        result.records_read = len(raw)
        logger.info("Extracted %d records from %s", len(raw), source_path)

        # Transform
        models = self.transform(raw)
        result.records_skipped = result.records_read - len(models)

        # Load
        result.records_stored = self.load(models)
        self.session.commit()

        logger.info(
            "Ingestion complete: %d read, %d stored, %d skipped",
            result.records_read, result.records_stored, result.records_skipped,
        )
        return result
