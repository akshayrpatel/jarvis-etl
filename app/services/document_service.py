import logging
from threading import Event

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from typing import Generator, List, Set

from app.config.core import document_service_config

logger = logging.getLogger(__name__)


class DocumentService:
	"""
  Service responsible for scanning files, loading raw documents,
  splitting them into chunks, and returning LangChain Document objects.

  Supports:
    - Filtering by allowed extensions
    - Pluggable file loaders
    - Batch or single-file processing
  """

	EXTENSION_LOADERS = {
		".txt": TextLoader
	}

	def __init__(self,
	             documents_path: Path = document_service_config.documents_path,
	             allowed_extensions: Set[str] = document_service_config.allowed_extensions):
		logger.info("[DocumentService] Initializing RecursiveCharacterTextSplitter (chunk_size=%d, chunk_overlap=%d)",
		            document_service_config.chunk_size, document_service_config.chunk_overlap)
		self.documents_path = documents_path
		self.allowed_extensions = allowed_extensions
		self.splitter = RecursiveCharacterTextSplitter(
			chunk_size=document_service_config.chunk_size,
			chunk_overlap=document_service_config.chunk_overlap,
		)
		logger.info("[DocumentService] Intialized")

	def is_valid_file(self, file: Path) -> bool:
		"""Return True if file is a real file and extension is allowed."""
		return file.is_file() and file.suffix.lower() in self.allowed_extensions

	def get_file_loader(self, file_path: Path) -> type[TextLoader] | None:
		"""Return the file loader class for a given file, or None if unsupported."""
		return self.EXTENSION_LOADERS.get(file_path.suffix.lower(), None)

	def load_and_split_file(self, file_path: Path) -> List[Document]:
		"""
    Load and split a single valid file into many chunked Document objects.

    Args:
        file_path: Path to the file

    Returns:
        A list of chunked Document objects.
    """

		if not self.is_valid_file(file_path):
			logger.debug("[DocumentService] Skipping invalid file: %s", file_path)
			return []

		file_loader_class = self.get_file_loader(file_path)
		if not file_loader_class:
			logger.warning("[DocumentService] No loader registered for file: %s", file_path)
			return []

		try:
			loader = file_loader_class(str(file_path))
			documents = loader.load()
			logger.info("[DocumentService] Loaded %d raw docs from %s", len(documents), file_path)

			chunks: List[Document] = []
			for doc in documents:
				splits = self.splitter.split_documents([doc])
				chunks.extend(splits)

			logger.info("[DocumentService] Produced %d chunks from %s", len(chunks), file_path)
			return chunks

		except Exception as ex:
			logger.exception("[DocumentService] Failed to process %s: %s", file_path, ex)
			return []

	def load_and_split_batch(self, batch_size: int | None) -> Generator[List[Document], None, None]:
		"""
    Load & split documents in a directory **in batches**.

    Args:
        batch_size: Number of raw documents before triggering split+yield

    Yields:
        A list of Document chunks (each chunk already split)
    """
		if batch_size is None:
			batch_size = document_service_config.batch_size
		directory: Path = self.documents_path
		batch: List[Document] = []

		logger.info("[DocumentService] Scanning directory for documents: %s", directory)

		for file_path in directory.rglob('*'):
			if not self.is_valid_file(file_path):
				logger.info("[DocumentService] Skipping invalid file: %s", file_path)
				continue

			file_loader = self.get_file_loader(file_path)
			if file_loader is None:
				logger.warning("[DocumentService] No loader registered for file: %s", file_path)
				continue

			try:
				loader = file_loader(str(file_path))
				logger.info("[DocumentService] Loaded raw docs from %s", file_path)

				raw = loader.load()
				splits = self.splitter.split_documents(raw)
				logger.info("[DocumentService] Produced %d splits from %s", len(splits), file_path)

				for split in splits:
					batch.append(split)
					if len(batch) >= batch_size:
						logger.info("[DocumentService] Yield batch of %d from %s", len(batch), file_path)
						yield batch
						batch.clear()

			except Exception as ex:
				logger.exception("[DocumentService] Failed to process %s: %s", file_path, ex)
				continue

		# Process any remaining documents in batch
		if batch:
			logger.info("[DocumentService] Yielding final batch of %d chunks", len(batch))
			yield batch
