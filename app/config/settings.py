import os

from enum import Enum
from pathlib import Path
from pydantic_settings import BaseSettings

APP_ROOT = Path(__file__).parents[2]

class AppMode(str, Enum):
	DEVELOPMENT = "development"
	PRODUCTION = "production"

def get_env() -> str:
	return os.getenv("APP_ENV", AppMode.DEVELOPMENT.value)

def load_env_file() -> Path:
	return APP_ROOT / f".env.{get_env()}"

class Settings(BaseSettings):
	# environment
	app_root: Path = APP_ROOT
	app_env: str = get_env()

	# Mistral
	mistral_api_key: str
	mistral_model_embed_name: str

	# Queue
	document_queue_url: str
	embedding_queue_url: str

	# vectordb
	vectordb_dir: str
	vectordb_host: str
	vectordb_port: int
	vectordb_collection_name: str

	model_config = {
		"env_file": load_env_file(),
		"env_file_encoding": "utf-8",
		"extra": "ignore",  # optional but recommended for clean loading
	}

settings = Settings()