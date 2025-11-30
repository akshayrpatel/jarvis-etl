import logging
import time

from threading import Thread
from typing import List, Dict, Any
from langchain_core.documents import Document

from app.config.core import embedding_service_config
from app.services.embedding_service import EmbeddingService
from app.services.queue_service import RedisBufferQueue

logger = logging.getLogger(__name__)


class EmbeddingWorker:
	"""
	Thin wrapper that repeatedly calls EmbeddingWorkerService.
	"""

	def __init__(self,
	             document_queue: RedisBufferQueue,
	             embedding_queue: RedisBufferQueue,
	             embedding_service: EmbeddingService,
	             batch_size: int = embedding_service_config.batch_size,
	             sleep_timer: int = embedding_service_config.sleep_timer) -> None:
		self.document_queue = document_queue
		self.embedding_queue: RedisBufferQueue = embedding_queue
		self.embedding_service = embedding_service
		self.thread = Thread(target=self.run, daemon=True, name="EmbeddingWorkerThread")
		self.running = True
		self.batch_size = batch_size
		self.sleep_timer = sleep_timer
		logger.info("[EmbeddingWorker] Initialized")

	def push_batch(self, vectors: List[List[float]], docs: List[Document]) -> None:
		"""
		Push embeddings + metadata to output queue.

		Args:
				vectors: List of embedding vectors.
				docs: List of original Documents (metadata will be included).
		"""
		batch_payload: List[Dict[str, Any]] = []
		for vector, doc in zip(vectors, docs):
			payload: Dict[str, Any] = {
				"vector": vector,
				"document": doc
			}
			batch_payload.append(payload)
		logger.info("[EmbeddingWorker] Pushing batch of %d embeddings to embedding queue",len(batch_payload))
		self.embedding_queue.push_batch(batch_payload)

	def start(self) -> None:
		"""Starts the worker thread."""
		logger.info("[EmbeddingWorker] Starting thread")
		self.thread.start()

	def stop(self) -> None:
		"""Signals the worker loop to stop."""
		self.running = False
		logger.warning("[EmbeddingWorker] Stop signal sent")

	def run(self) -> None:
		"""Main worker loop."""
		logger.info("[EmbeddingWorker] Started")

		while self.running:
			docs: List[Document] = self.document_queue.pop_batch(self.batch_size)

			if docs is None:
				logger.info("[EmbeddingWorker] All documents are now embedded, exiting...")
				self.embedding_queue.push_batch(None)
				break

			if len(docs) == 0:
				logger.info("[EmbeddingWorker] No documents available. Worker now idling for new documents")
				time.sleep(self.sleep_timer)
				continue

			vectors = self.embedding_service.embed_batch(docs)
			logger.info("[EmbeddingWorker] Embeddings generated, pushing batch of %d embeddings to embedding_queue", len(vectors))
			self.push_batch(vectors, docs)

			logger.info("[EmbeddingWorker] Pushed a batch of embeddings, worker now idling for new documents")
			time.sleep(self.sleep_timer)

		logger.info("[EmbeddingWorker] Worker stopped cleanly")
