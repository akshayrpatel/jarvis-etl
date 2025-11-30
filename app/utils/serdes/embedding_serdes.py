from langchain_core.documents import Document

from app.utils.serdes.serdes_protocol import SerDesProtocol
from typing import Dict, Any
import json

class EmbeddingSerDes(SerDesProtocol):
	"""Handles serialization and deserialization for Embedding (List[float]) objects."""

	# Type Hinting for clarity, ensuring the type T is List[float]
	T = Dict[str, Any]

	def serialize(self, item: T) -> str:
		"""
    Serializes the payload dictionary. Must convert the 'document' field
    (a Document object) to a dictionary first.
    """
		# 1. Extract the Document object
		doc: Document = item.get("document")

		# 2. Recreate the payload with the Document object converted to its JSON-compatible parts
		json_payload = {
			"vector": item.get("vector"),
			"document": {
				"page_content": doc.page_content,
				"metadata": doc.metadata
			}
		}
		return json.dumps(json_payload)

	def deserialize(self, json_str: str) -> T:
		"""
    Deserializes the JSON string back to the payload dictionary,
    recreating the Document object.
    """
		data: Dict[str, Any] = json.loads(json_str)

		# Reconstruct the Document object from its parts
		doc = Document(
			page_content=data['document']['page_content'],
			metadata=data['document']['metadata']
		)

		# Recreate the final payload dictionary
		return {
			"vector": data['vector'],
			"document": doc
		}