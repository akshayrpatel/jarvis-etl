from typing import Protocol, TypeVar, List, Any

# Define a generic type for the data being handled
T = TypeVar('T')

class SerDesProtocol(Protocol):
    """
    Protocol defining the required interface for all Serializer/Deserializer classes.
    """
    def serialize(self, item: T) -> str:
        """Converts an object T to a string (for storage/transmission)."""
        ...

    def deserialize(self, data: str) -> T:
        """Converts a string back to an object T."""
        ...