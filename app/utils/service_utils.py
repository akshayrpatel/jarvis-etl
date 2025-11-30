from pathlib import Path
from app.config.core import document_service_config


def get_category_from_path(file_path: Path, base_path: Path = document_service_config.documents_path) -> str:
	# Get relative path parts from base_path
	relative_parts = file_path.relative_to(base_path).parts

	# The first part of the relative path is the category
	if relative_parts:
		category = relative_parts[0]
		return category
	return ""
