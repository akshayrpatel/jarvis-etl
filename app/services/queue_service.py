import logging
import time
import redis

from typing import List, TypeVar, Callable
from redis import Redis
from app.config.core import redis_config

T = TypeVar('T')
logger = logging.getLogger(__name__)

SENTINEL_STR = "__SENTINEL__"
SENTINEL_BYTES = SENTINEL_STR.encode("utf-8")

class RedisBufferQueue:

	def __init__(self,
	             redis_url: str,
	             queue_name: str,
	             serializer: Callable[[T], str],
	             deserializer: Callable[[str], T]) -> None:
		self.redis_url = redis_url
		self.queue_name = queue_name
		self.serializer = serializer
		self.deserializer = deserializer
		self.redis_client = self.get_redis_client()

	def get_redis_client(self) -> Redis | None:
		for attempt in range(redis_config.max_retries):
			try:
				client = redis.Redis.from_url(
					self.redis_url,
					socket_keepalive=True,
					socket_timeout=5
				)

				client.ping()
				logger.info("[QueueService] Redis client initialized and connected successfully.")
				return client
			except ConnectionError as e:
				logger.warning(f"[QueueService] Redis connection attempt {attempt + 1} failed: {e}")
				if attempt < redis_config.max_retries:
					time.sleep(redis_config.sleep_timer)
					return None
				else:
					raise
		return None

	def push_batch(self, items: List[T] | None) -> None:
		"""
		Push multiple items to the queue at once.
		"""
		if items is None:
			self.redis_client.rpush(self.queue_name, SENTINEL_BYTES)
			return
		pipeline = self.redis_client.pipeline()
		for item in items:
			pipeline.rpush(self.queue_name, self.serializer(item))
		pipeline.execute()

	def pop_batch(self, batch_size: int = 10) -> List[T] | None:
		"""
		Pop a batch of items from the queue.
		"""
		batch = []
		for attempt in range(redis_config.max_retries):
			try:
				pipeline = self.redis_client.pipeline()
				for _ in range(batch_size):
					pipeline.lpop(self.queue_name)
				raw_items = pipeline.execute()

				for item_bytes in raw_items:
					if item_bytes is None:
						return batch
					if item_bytes == SENTINEL_BYTES:
						return None
					if item_bytes:
						batch.append(self.deserializer(item_bytes))
				return batch

			except ConnectionError as e:
				logger.error(f"[QueueService] Connection lost during pop_batch from {self.queue_name}, retry: {e}")
				self.redis_client = self.get_redis_client()

		return batch

	def size(self) -> int:
		"""
		Returns the size of the queue.
		"""
		return self.redis_client.llen(self.queue_name)

	def clear(self) -> None:
		"""
		Clear the queue.
		"""
		self.redis_client.delete(self.queue_name)
