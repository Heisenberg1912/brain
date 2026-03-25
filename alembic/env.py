from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from brain.database import Base
from brain.config import settings

# Import all models so they register with Base.metadata
from brain.data_bank.models import (
    Location,
    Masterplan,
    PropertyPrice,
    Infrastructure,
    CensusData,
    LocationGeoProfile,
    RegionalStandard,
    PlanningContext,
)
from brain.valuation.models import ValuationScore
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

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Enable PostGIS extension
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.commit()

        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
