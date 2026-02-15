"""Safe serialization utilities for state management."""

import json
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


class SafeJSONEncoder(json.JSONEncoder):
    """
    Safe JSON encoder that handles common Python types.

    This replaces pickle serialization to avoid security vulnerabilities
    while still supporting common types like datetime, Decimal, etc.
    """

    def default(self, obj: Any) -> Any:
        """Encode non-standard types to JSON-compatible formats."""
        # Datetime types
        if isinstance(obj, (datetime, date)):
            return {"__type__": "datetime", "value": obj.isoformat()}

        # Numeric types
        if isinstance(obj, Decimal):
            return {"__type__": "Decimal", "value": str(obj)}

        # UUID
        if isinstance(obj, UUID):
            return {"__type__": "UUID", "value": str(obj)}

        # Path
        if isinstance(obj, Path):
            return {"__type__": "Path", "value": str(obj)}

        # Enum
        if isinstance(obj, Enum):
            return {"__type__": "Enum", "name": obj.__class__.__name__, "value": obj.value}

        # Bytes
        if isinstance(obj, bytes):
            return {"__type__": "bytes", "value": obj.hex()}

        # Set
        if isinstance(obj, set):
            return {"__type__": "set", "value": list(obj)}

        # Pydantic models
        if hasattr(obj, "model_dump"):
            return {"__type__": "pydantic", "value": obj.model_dump()}

        # Fallback: convert to string representation
        try:
            return {"__type__": "str_repr", "value": str(obj), "class": obj.__class__.__name__}
        except Exception:
            return {"__type__": "unserializable", "class": obj.__class__.__name__}


def safe_json_decode(dct: dict) -> Any:
    """
    Custom JSON decoder that reconstructs typed objects.

    Args:
        dct: Dictionary potentially containing type information

    Returns:
        Reconstructed object or original dict
    """
    if "__type__" not in dct:
        return dct

    obj_type = dct["__type__"]
    value = dct.get("value")

    # Datetime
    if obj_type == "datetime":
        return datetime.fromisoformat(value)

    # Decimal
    if obj_type == "Decimal":
        return Decimal(value)

    # UUID
    if obj_type == "UUID":
        return UUID(value)

    # Path
    if obj_type == "Path":
        return Path(value)

    # Bytes
    if obj_type == "bytes":
        return bytes.fromhex(value)

    # Set
    if obj_type == "set":
        return set(value)

    # Pydantic (return as dict, can't reconstruct without model class)
    if obj_type == "pydantic":
        return value

    # String representation (return as-is)
    if obj_type == "str_repr":
        return value

    # Unserializable (return dict with metadata)
    return dct


def safe_serialize(obj: Any) -> str:
    """
    Safely serialize an object to JSON string.

    Args:
        obj: Object to serialize

    Returns:
        JSON string

    Raises:
        ValueError: If serialization fails
    """
    try:
        return json.dumps(obj, cls=SafeJSONEncoder, indent=None)
    except Exception as e:
        raise ValueError(f"Failed to serialize object: {e}") from e


def safe_deserialize(data: str) -> Any:
    """
    Safely deserialize a JSON string to object.

    Args:
        data: JSON string

    Returns:
        Deserialized object

    Raises:
        ValueError: If deserialization fails
    """
    try:
        return json.loads(data, object_hook=safe_json_decode)
    except Exception as e:
        raise ValueError(f"Failed to deserialize data: {e}") from e


def safe_serialize_bytes(obj: Any) -> bytes:
    """
    Safely serialize an object to JSON bytes.

    Args:
        obj: Object to serialize

    Returns:
        JSON bytes
    """
    return safe_serialize(obj).encode("utf-8")


def safe_deserialize_bytes(data: bytes) -> Any:
    """
    Safely deserialize JSON bytes to object.

    Args:
        data: JSON bytes

    Returns:
        Deserialized object
    """
    return safe_deserialize(data.decode("utf-8"))
