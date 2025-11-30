import logging
import time

from threading import Thread
from app.config.core import document_service_config
from app.services.document_service import DocumentService
from app.services.queue_service import RedisBufferQueue

logger = logging.getLogger(__name__)


class DocumentWorker:
	"""
  Background worker responsible for:
      1. Running DocumentService to create chunks
      2. Pushing these chunks to the Redis 'document_queue'
      3. Running continuously (future: watcher for new files)

  This worker is always run in its own thread.
  """

	def __init__(self,
	             doc_queue: RedisBufferQueue,
	             doc_service: DocumentService,
	             batch_size: int = document_service_config.batch_size,
	             sleep_timer: int = document_service_config.sleep_timer):
		self.doc_queue = doc_queue
		self.doc_service = doc_service
		self.thread = Thread(target=self.run, daemon=True, name="DocumentWorkerThread")
		self.running = True
		self.batch_size = batch_size
		self.sleep_timer = sleep_timer
		logger.info("[DocumentWorker] Initialized")

	def start(self) -> None:
		"""Starts the worker thread."""
		logger.info("[DocumentWorker] Starting thread")
		self.thread.start()

	def stop(self) -> None:
		"""Signals the worker loop to stop."""
		self.running = False
		logger.warning("[DocumentWorker] Stop signal sent")

	def run(self) -> None:
		"""Main worker loop."""
		logger.info("[DocumentWorker] Started")

		for batch in self.doc_service.load_and_split_batch(batch_size=self.batch_size):
			logger.info("[DocumentWorker] Pushing batch of %d chunks to document_queue", len(batch))
			self.doc_queue.push_batch(batch)
			logger.info("[DocumentWorker] Worker now idling for %d seconds before pushing new batch", self.sleep_timer)
			time.sleep(self.sleep_timer)

		logger.info("[DocumentWorker] All documents are now processed, exiting...")
		self.doc_queue.push_batch(None)
		logger.info("[DocumentWorker] Worker stopped cleanly")