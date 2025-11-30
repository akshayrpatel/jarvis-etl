from app.config.vector_config import vector_config, VectorDbMode
from langchain_core.documents import Document
from pathlib import Path
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from typing import List
import chromadb
import uuid

class VectorStoreService:

	def __init__(self,
							 mode: str = VectorDbMode.LOCAL,
							 persist_directory: Path = vector_config.persist_directory,
							 host: str = 'localhost',
							 port: int = 8090,
							 ssl: bool = False,
							 collection_name: str = 'jarvis_data'):

		self.mode: str = mode
		self.persist_directory: Path = persist_directory

		self.host: str = host
		self.port: int = port
		self.ssl: bool = ssl
		self.vectordb_client: ClientAPI = self.create_client()

		self.collection_name: str = collection_name
		self.collection: Collection = self.create_collection()

	def create_client(self) -> ClientAPI:

		if self.mode == VectorDbMode.LOCAL:
			print(self.persist_directory)
			self.persist_directory.mkdir(parents=True, exist_ok=True)
			return chromadb.PersistentClient(
				path=self.persist_directory,
			)

		elif self.mode == VectorDbMode.SERVER:
			if not self.host or not self.port:
				raise ValueError('host and port are required')
			return chromadb.HttpClient(host=self.host, port=self.port, ssl=self.ssl)

		else:
			raise ValueError('invalid mode')

	def create_collection(self) -> Collection:
			return self.vectordb_client.get_or_create_collection(self.collection_name)

	def save_embeddings(self,
											embeddings: List[List[float]],
											documents: List[Document]) -> None:

		ids = [str(uuid.uuid4()) for _ in documents]
		metadatas = [doc.metadata for doc in documents]
		documents = [doc.page_content for doc in documents]

		self.collection.add(
			ids=ids,
			embeddings=embeddings,
			documents=documents,
			metadatas=metadatas,
		)

