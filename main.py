import logging
import time

from threading import Event

from app.config.settings import settings
from app.config.core import (document_service_config,
                             vectordb_service_config,
                             document_queue_config,
                             embedding_queue_config,
                             pipeline_config)
from app.config.logging_config import configure_logging

from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.queue_service import RedisBufferQueue
from app.services.vectordb_service import VectorDBService

from app.utils.serdes.document_serdes import DocumentSerDes
from app.utils.serdes.embedding_serdes import EmbeddingSerDes

from app.workers.document_worker import DocumentWorker
from app.workers.embedding_worker import EmbeddingWorker
from app.workers.vectordb_worker import VectorDBWorker

logger = logging.getLogger(__name__)

class Pipeline:
	"""
  Coordinates and runs all ETL pipeline workers.

  - DocumentWorker: reads files → chunks → pushes into document_queue
  - EmbeddingWorker: pulls chunks from document_queue → embeds → pushes into embedding_queue
  - VectorDBWorker: pulls embedded vectors → stores in Vector DB
  """

	def __init__(self,
	             document_queue: RedisBufferQueue,
	             embedding_queue: RedisBufferQueue,
	             document_service: DocumentService,
	             embedding_service: EmbeddingService,
	             vectordb_service: VectorDBService,
	             complete_event: Event):
		logger.info("[Pipeline] Initializing ETL Pipeline...")
		self.document_worker = DocumentWorker(document_queue, document_service)
		self.embedding_worker = EmbeddingWorker(document_queue, embedding_queue, embedding_service)
		self.vectordb_worker = VectorDBWorker(embedding_queue, vectordb_service, complete_event=complete_event)
		self.workers = [
			self.document_worker,
			self.embedding_worker,
			self.vectordb_worker
		]
		self.complete_event = complete_event
		logger.info("[Pipeline] ETL Pipeline initialized with 3 workers")

	def start(self) -> None:
		"""Start all workers."""
		logger.info("[Pipeline] Starting all workers...")
		for worker in self.workers:
			worker.start()
			logger.info(f"[Pipeline] Started worker: {worker.__class__.__name__}")
			time.sleep(pipeline_config.worker_delay)

		logger.info("[Pipeline] All workers are now running.")

	def stop(self) -> None:
		"""
    Signals all workers to stop and waits for them to exit.
    """
		logger.warning("[Pipeline] Stop signal issued. Stopping workers...")

		# 1. Signal all workers to stop
		for worker in self.workers:
			worker.stop()

		# 2. Join (wait for) all worker threads to finish their current job and exit
		for worker in self.workers:
			worker.thread.join()
			logger.info(f"[Pipeline] Worker stopped: {worker.__class__.__name__}")

		logger.info("[Pipeline] All workers have successfully stopped.")

if __name__ == "__main__":
	logger.info("[Main] Starting Jarvis ETL Pipeline in %s environment.", settings.app_env)
	configure_logging()

	pipeline_complete_event = Event()

	doc_queue = RedisBufferQueue(
		redis_url=document_queue_config.queue_url,
		queue_name=document_queue_config.queue_name,
		serializer=DocumentSerDes().serialize,
		deserializer=DocumentSerDes().deserialize
	)

	embed_queue = RedisBufferQueue(
		redis_url=embedding_queue_config.queue_url,
		queue_name=embedding_queue_config.queue_name,
		serializer=EmbeddingSerDes().serialize,
		deserializer=EmbeddingSerDes().deserialize
	)

	doc_service = DocumentService(
		documents_path=document_service_config.documents_path,
		allowed_extensions=document_service_config.allowed_extensions
	)

	embed_service = EmbeddingService()

	db_service = VectorDBService(
		mode=vectordb_service_config.mode,
		persist_directory=vectordb_service_config.persist_directory,
		host=vectordb_service_config.host,
		port=vectordb_service_config.port,
		ssl=vectordb_service_config.ssl,
		collection_name=vectordb_service_config.collection_name
	)

	jarvis_data_pipeline: Pipeline = Pipeline(
		complete_event=pipeline_complete_event,
		document_queue=doc_queue,
		embedding_queue=embed_queue,
		document_service=doc_service,
		embedding_service=embed_service,
		vectordb_service=db_service
	)

	try:
		# Start pipeline
		jarvis_data_pipeline.start()

		# Wait until complete event received
		jarvis_data_pipeline.complete_event.wait()

		# Stop pipeline
		jarvis_data_pipeline.stop()

	except KeyboardInterrupt:
		# This block runs when the user presses Ctrl+C
		logger.warning("[Main] Keyboard Interrupt received. Shutting down gracefully...")
		jarvis_data_pipeline.stop()

	except Exception as e:
		logger.exception(f"[Main] Unexpected error occurred: {e}")
		jarvis_data_pipeline.stop()

	logger.info("[Main] ETL Pipeline has shut down.")