from app.utils.serdes.serdes_protocol import SerDesProtocol
from langchain_core.documents import Document

class DocumentSerDes(SerDesProtocol):
	"""Handles serialization and deserialization for LangChain Document objects."""

	# Type Hinting for clarity, ensuring the type T is Document
	T = Document

	def serialize(self, document: Document) -> str:
		"""Serializes a Document to a JSON string."""
		return document.model_dump_json()

	def deserialize(self, json_str: str) -> Document:
		"""Deserializes a JSON string back to a Document object."""
		return Document.model_validate_json(json_str)