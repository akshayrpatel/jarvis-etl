import logging

from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings
from typing import List

from app.config.core import embedding_service_config

logger = logging.getLogger(__name__)


class EmbeddingService:
	"""
  Service responsible for converting batches of LangChain Document objects
  into embedding vectors using the configured embedding model.
  """

	def __init__(self) -> None:
		logger.info("[EmbeddingService] Initializing MistralAIEmbeddingsModel")
		self.embedding_model = MistralAIEmbeddings(
			api_key=embedding_service_config.api_key,
			model=embedding_service_config.embedding_model_name
		)
		logger.info("[EmbeddingService] Initialized")

	def embed_batch(self, docs: List[Document]) -> List[List[float]]:
		"""
    Generate embeddings for a batch of Document objects.

    Args:
        docs: A list of Document objects to embed.

    Returns:
        A list where each item is a float vector representing the embedding for one document.
    """
		if not docs:
			logger.warning("[EmbeddingService] No docs to embed")
			return []

		texts: List[str] = [doc.page_content for doc in docs]
		logger.info("[EmbeddingService] Embedding %d documents", len(docs))

		try:
			vectors: List[List[float]] = self.embedding_model.embed_documents(texts)
			logger.info("[EmbeddingService] Embedded %d documents", len(docs))
			return vectors
		except Exception as ex:
			logger.exception("[EmbeddingService] Failed to embed batch: %s", ex)
			return []


