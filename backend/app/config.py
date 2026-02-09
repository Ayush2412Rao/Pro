import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    azure_api_key: str
    azure_endpoint: str
    azure_api_version: str
    azure_deployment: str
    azure_embeddings_deployment: str | None
    hf_embeddings_model: str | None
    db_path: Path
    data_dir: Path


def get_settings() -> Settings:
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "").strip()
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
    azure_embeddings_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "").strip()
    hf_embeddings_model = os.getenv("HF_EMBEDDINGS_MODEL", "").strip()

    if not azure_api_key or not azure_endpoint or not azure_api_version or not azure_deployment:
        raise RuntimeError(
            "Missing Azure OpenAI configuration. "
            "Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT."
        )
    if not azure_embeddings_deployment and not hf_embeddings_model:
        raise RuntimeError(
            "Missing embeddings configuration. Set either "
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT or HF_EMBEDDINGS_MODEL."
        )

    db_path_env = os.getenv("APP_DB_PATH", str(BASE_DIR / "data" / "complaints.db"))

    return Settings(
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        azure_deployment=azure_deployment,
        azure_embeddings_deployment=azure_embeddings_deployment or None,
        hf_embeddings_model=hf_embeddings_model or None,
        db_path=Path(db_path_env),
        data_dir=BASE_DIR / "data",
    )
