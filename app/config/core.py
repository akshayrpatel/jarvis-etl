from enum import Enum
from pathlib import Path

from app.config.settings import settings, AppMode


class DocumentServiceConfig:
	documents_path: Path = settings.app_root / 'data'
	allowed_extensions: tuple = (".txt", ".md", ".json")
	chunk_size: int = 500
	chunk_overlap: int = 50
	batch_size: int = 50
	sleep_timer: int = 120


class EmbeddingServiceConfig:
	embedding_model_name: str = settings.mistral_model_embed_name
	api_key: str = settings.mistral_api_key
	batch_size: int = 50
	sleep_timer: int = 120


class VectorDBMode(str, Enum):
	LOCAL = "local"
	SERVER = "server"

class VectorDBServiceConfig:
	mode: str = VectorDBMode.SERVER if settings.app_env == AppMode.PRODUCTION else VectorDBMode.LOCAL
	persist_directory: Path = settings.app_root / 'db'
	host: str = settings.vectordb_host
	port: int = settings.vectordb_port
	ssl: bool = True if settings.app_env == AppMode.PRODUCTION else False
	collection_name: str = settings.vectordb_collection_name
	batch_size: int = 50
	sleep_timer: int = 120

############################################

class RedisConfig:
	max_retries: int = 3
	sleep_timer: int = 3

class DocumentQueueConfig:
	queue_url: str = settings.document_queue_url
	queue_name: str = 'document_queue'

class EmbeddingQueueConfig:
	queue_url: str = settings.embedding_queue_url
	queue_name: str = 'embedding_queue'

class PipelineConfig:
	worker_delay: int = 3


pipeline_config: PipelineConfig = PipelineConfig()
redis_config: RedisConfig = RedisConfig()
document_queue_config = DocumentQueueConfig()
embedding_queue_config = EmbeddingQueueConfig()
document_service_config = DocumentServiceConfig()
embedding_service_config = EmbeddingServiceConfig()
vectordb_service_config = VectorDBServiceConfig()

