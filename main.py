from app.config import document_queue_config, embedding_queue_config, document_config, vectordb_config
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.queue_service import RedisBufferQueue
from app.services.vectordb_service import VectorDBService
from app.utils.serdes.document_serdes import DocumentSerDes
from app.utils.serdes.embedding_serdes import EmbeddingSerDes
from app.workers.document_worker import DocumentWorker
from app.workers.embedding_worker import EmbeddingWorker
from app.workers.vectordb_worker import VectorDBWorker

class Pipeline:
	"""
	Orchestrate all services and workers
	"""

	def __init__(self,
	             document_queue: RedisBufferQueue,
	             embedding_queue: RedisBufferQueue,
	             document_service: DocumentService,
	             embedding_service: EmbeddingService,
	             vectordb_service: VectorDBService):
		self.document_worker = DocumentWorker(document_queue, document_service)
		self.embedding_worker = EmbeddingWorker(document_queue, embedding_queue, embedding_service)
		self.vectordb_worker = VectorDBWorker(embedding_queue, vectordb_service)

	def start(self) -> None:
		print("[ETLPipeline] Starting all workers...")
		self.document_worker.start()
		self.embedding_worker.start()
		self.vectordb_worker.start()
		print("[ETLPipeline] Workers are now running.")

if __name__ == "__main__":
	doc_queue = RedisBufferQueue(
		redis_url=document_queue_config.DOCUMENT_QUEUE_URL,
		queue_name=document_queue_config.queue_name,
		serializer=DocumentSerDes().serialize,
		deserializer=DocumentSerDes().deserialize
	)

	embed_queue = RedisBufferQueue(
		redis_url=embedding_queue_config.EMBEDDING_QUEUE_URL,
		queue_name=embedding_queue_config.queue_name,
		serializer=EmbeddingSerDes().serialize,
		deserializer=EmbeddingSerDes().deserialize
	)

	doc_service = DocumentService(
		documents_path=document_config.documents_path,
		allowed_extensions=document_config.allowed_extensions
	)

	embed_service = EmbeddingService()

	db_service = VectorDBService(
		mode=vectordb_config.vectordb_mode,
		persist_directory=vectordb_config.persist_directory,
		host=vectordb_config.host,
		port=vectordb_config.port,
		ssl=vectordb_config.ssl,
		collection_name=vectordb_config.collection_name
	)

	jarvis_data_pipeline: Pipeline = Pipeline(
		document_queue=doc_queue,
		embedding_queue=embed_queue,
		document_service=doc_service,
		embedding_service=embed_service,
		vectordb_service=db_service
	)

	jarvis_data_pipeline.start()