import logging
import chromadb
import uuid

from langchain_core.documents import Document
from pathlib import Path
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from typing import List, Dict, Any

from app.config.core import VectorDBMode, vectordb_service_config
from app.utils import service_utils

logger = logging.getLogger(__name__)


class VectorDBService:
	"""
  Wrapper around ChromaDB for saving document embeddings.
  Supports both:
      - local persistent mode
      - remote HTTP server mode
  """

	def __init__(self,
							 mode: str = VectorDBMode.LOCAL,
							 persist_directory: Path = vectordb_service_config.persist_directory,
							 host: str = 'localhost',
							 port: int = 8000,
							 ssl: bool = False,
							 collection_name: str = vectordb_service_config.collection_name):

		logger.info("[VectorDBService] Initializing (mode=%s, collection=%s)",mode, collection_name)
		self.mode: str = mode
		self.persist_directory: Path = persist_directory

		self.host: str = host
		self.port: int = port
		self.ssl: bool = ssl
		self.client: ClientAPI | None = None

		self.collection_name: str = collection_name
		self.collection: Collection | None = None
		logger.info("[VectorDBService] Initialized (lazy)")

	def _initialize_db_connection(self):
		logger.info("[VectorDBService] Initializing db client and collection")
		if self.client is not None:
			return

		self.client = self._create_client()
		self.collection = self._create_collection(self.collection_name)

	def _create_client(self) -> ClientAPI:
		"""
    Create either a local ChromaDB client or a remote HTTP client.
    """

		if self.mode == VectorDBMode.LOCAL:
			logger.info("[VectorDBService] Using local persistent ChromaDB at %s", self.persist_directory)
			self.persist_directory.mkdir(parents=True, exist_ok=True)
			return chromadb.PersistentClient(
				path=self.persist_directory,
			)

		elif self.mode == VectorDBMode.SERVER:
			if not self.host or not self.port:
				logger.exception("[VectorDBService] Unable to connect to remote ChromaDB server without host and port")
				raise ValueError('host and port are required')

			logger.info(
				"[VectorDBService] Connecting to remote ChromaDB server: %s:%s (ssl=%s)",
				self.host, self.port, self.ssl
			)
			return chromadb.HttpClient(host=self.host, port=self.port, ssl=self.ssl)

		else:
			logger.exception("[VectorDBService] Invalid vectordb mode: %s", self.mode)
			raise ValueError('invalid mode')

	def _create_collection(self, collection_name: str) -> Collection:
		"""
		Create collection if missing; otherwise returns existing one.
		"""
		try:
			logger.info("[VectorDBService] Using collection %s", collection_name)
			return self.client.get_or_create_collection(collection_name)
		except Exception:
			logger.exception("[VectorDBService] Failed to create or access collection")
			raise

	def _get_metadatas(self, documents: List[Document]) -> List[Dict[str, Any]]:
		logger.info("[VectorDBService] Creating custom metadatas")
		metadatas = []
		for doc in documents:
			metadata: Dict[str, Any] = doc.metadata
			source: str = metadata['source']
			source_file_path: Path = Path(source)
			category = service_utils.get_category_from_path(source_file_path)
			if category:
				metadata['category'] = category
				metadatas.append(metadata)
		return metadatas

	def save_embeddings(self,
											embeddings: List[List[float]],
											documents: List[Document]) -> None:
		"""
    Save embeddings + metadata into ChromaDB.

    Args:
        embeddings: List of float vectors
        documents: Corresponding LangChain Document objects
    """
		if self.client is None:
			self._initialize_db_connection()

		if not embeddings or not documents:
			logger.warning("[VectorDBService] save_embeddings() called with empty inputs")
			return

		ids = [str(uuid.uuid4()) for _ in documents]
		metadatas = self._get_metadatas(documents)
		documents = [doc.page_content for doc in documents]

		try:
			self.collection.add(
				ids=ids,
				embeddings=embeddings,
				documents=documents,
				metadatas=metadatas,
			)
			logger.info("[VectorDBService] Saved %d embeddings to collection %s",len(embeddings), self.collection_name)
		except Exception as ex:
			logger.exception("[VectorDBService] Failed to save embeddings to ChromaDB", ex)
