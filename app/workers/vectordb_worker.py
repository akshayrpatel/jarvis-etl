import logging
import time

from threading import Thread, Event
from langchain_core.documents import Document
from typing import List, Dict, Any

from app.config.core import vectordb_service_config
from app.services.queue_service import RedisBufferQueue
from app.services.vectordb_service import VectorDBService

logger = logging.getLogger(__name__)


class VectorDBWorker:
	"""
  Worker responsible for:
      1. Reading embedded documents from the embedding queue.
      2. Saving embeddings + metadata to ChromaDB.

  Runs as a background daemon thread.
  """

	def __init__(self,
	             embedding_queue: RedisBufferQueue,
	             vectordb_service: VectorDBService,
	             batch_size: int = vectordb_service_config.batch_size,
	             sleep_timer: int = vectordb_service_config.sleep_timer,
	             complete_event: Event = None) -> None:
		self.embedding_queue = embedding_queue
		self.vectordb_service = vectordb_service
		self.thread = Thread(target=self.run, daemon=True, name="VectorDBWorkerThread")
		self.running = True
		self.batch_size = batch_size
		self.sleep_timer = sleep_timer
		self.complete_event = complete_event
		logger.info("[VectorDBWorker] Initialized")

	def start(self) -> None:
		"""Starts the worker thread."""
		logger.info("[VectorDBWorker] Starting thread")
		self.thread.start()

	def stop(self) -> None:
		"""Signals the worker loop to stop."""
		self.running = False
		logger.warning("[VectorDBWorker] Stop signal sent")

	def run(self) -> None:
		"""Main worker loop."""
		logger.info("[VectorDBWorker] Started")

		while self.running:
			batch: List[Dict[str, Any]] = self.embedding_queue.pop_batch(self.batch_size)

			if batch is None:
				logger.info("[VectorDBWorker] All embeddings are saved, exiting...")
				self.complete_event.set()
				break

			if len(batch) == 0:
				logger.info("[VectorDBWorker] No embedding batch available. Worker now idling for new embeddings")
				time.sleep(self.sleep_timer)
				continue

			vectors: List[List[float]] = []
			documents: List[Document] = []
			for data in batch:
				vectors.append(data['vector'])
				documents.append(data['document'])

			logger.info("[VectorDBWorker] Saving %d embeddings to ChromaDB", len(documents))
			try:
				self.vectordb_service.save_embeddings(vectors, documents)
			except Exception as ex:
				logger.exception("[VectorDBWorker] Failed to commit embeddings", ex)
				continue
			logger.info("[VectorDBWorker] Successfully committed %d embeddings.", len(documents))

		logger.info("[VectorDBWorker] Worker stopped cleanly.")