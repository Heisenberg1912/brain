from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Google retired unversioned 1.x model ids on the Generative Language API; map common env values.
_LEGACY_GEMINI_MODEL_ALIASES: dict[str, str] = {
    "gemini-1.5-flash": "gemini-2.5-flash",
    "gemini-1.5-flash-8b": "gemini-2.5-flash",
    "gemini-1.5-flash-latest": "gemini-2.5-flash",
    "gemini-1.5-pro": "gemini-2.5-pro",
    "gemini-1.5-pro-latest": "gemini-2.5-pro",
    "gemini-1.0-pro": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-flash",
}


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

    @field_validator("gemini_model")
    @classmethod
    def _remap_legacy_gemini_model(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        return _LEGACY_GEMINI_MODEL_ALIASES.get(v.strip().lower(), v)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

PROJECT_ROOT = Path(__file__).parent.parent
SEED_DATA_DIR = PROJECT_ROOT / "seed_data"
