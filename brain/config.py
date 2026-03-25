from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "postgresql://builtattic:builtattic_dev@localhost:5432/builtattic_brain"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"  # "openai", "claude", or "gemini"
    openai_model: str = "gpt-4o"
    openai_base_url: str = ""
    claude_model: str = "claude-sonnet-4-5"
    gemini_model: str = "gemini-2.5-pro"
    supported_plan_chains: str = "polygon,base"
    default_plan_chain: str = "polygon"
    storage_backend: str = "ipfs"
    ipfs_gateway_base: str = "https://ipfs.io/ipfs"
    weights_file: str = "scoring_weights.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

PROJECT_ROOT = Path(__file__).parent.parent
SEED_DATA_DIR = PROJECT_ROOT / "seed_data"
