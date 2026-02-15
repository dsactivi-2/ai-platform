"""Tests for safe serialization."""

from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from governor.utils.serialization import (
    safe_serialize,
    safe_deserialize,
    safe_serialize_bytes,
    safe_deserialize_bytes,
)


def test_serialize_basic_types():
    """Test serialization of basic Python types."""
    data = {
        "string": "hello",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
    }

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert deserialized == data


def test_serialize_datetime():
    """Test serialization of datetime objects."""
    now = datetime(2025, 1, 15, 12, 30, 45)
    data = {"timestamp": now}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["timestamp"], datetime)
    assert deserialized["timestamp"] == now


def test_serialize_date():
    """Test serialization of date objects."""
    today = date(2025, 1, 15)
    data = {"date": today}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["date"], date)


def test_serialize_decimal():
    """Test serialization of Decimal objects."""
    amount = Decimal("123.45")
    data = {"amount": amount}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["amount"], Decimal)
    assert deserialized["amount"] == amount


def test_serialize_uuid():
    """Test serialization of UUID objects."""
    id_value = UUID("12345678-1234-5678-1234-567812345678")
    data = {"id": id_value}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["id"], UUID)
    assert deserialized["id"] == id_value


def test_serialize_path():
    """Test serialization of Path objects."""
    path = Path("/tmp/test.txt")
    data = {"path": path}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["path"], Path)
    assert deserialized["path"] == path


def test_serialize_bytes():
    """Test serialization of bytes objects."""
    data_bytes = b"hello world"
    data = {"data": data_bytes}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["data"], bytes)
    assert deserialized["data"] == data_bytes


def test_serialize_set():
    """Test serialization of set objects."""
    data_set = {1, 2, 3}
    data = {"numbers": data_set}

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert isinstance(deserialized["numbers"], set)
    assert deserialized["numbers"] == data_set


def test_serialize_bytes_methods():
    """Test byte-based serialization methods."""
    data = {"key": "value", "number": 42}

    serialized_bytes = safe_serialize_bytes(data)
    assert isinstance(serialized_bytes, bytes)

    deserialized = safe_deserialize_bytes(serialized_bytes)
    assert deserialized == data


def test_serialize_nested_structures():
    """Test serialization of nested data structures."""
    data = {
        "users": [
            {"name": "Alice", "created": datetime(2025, 1, 1)},
            {"name": "Bob", "created": datetime(2025, 1, 2)},
        ],
        "metadata": {
            "version": Decimal("1.0"),
            "id": UUID("12345678-1234-5678-1234-567812345678"),
        },
    }

    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    assert len(deserialized["users"]) == 2
    assert isinstance(deserialized["users"][0]["created"], datetime)
    assert isinstance(deserialized["metadata"]["version"], Decimal)
    assert isinstance(deserialized["metadata"]["id"], UUID)


def test_serialize_complex_types_fallback():
    """Test that complex non-serializable types fall back gracefully."""

    class CustomClass:
        def __init__(self):
            self.value = 42

        def __str__(self):
            return f"CustomClass(value={self.value})"

    obj = CustomClass()
    data = {"custom": obj}

    # Should not raise, should use fallback
    serialized = safe_serialize(data)
    deserialized = safe_deserialize(serialized)

    # Fallback converts to string representation
    assert "custom" in deserialized


def test_serialize_invalid_data_raises():
    """Test that invalid serialization raises ValueError."""
    # Create a circular reference which JSON can't handle
    circular = {}
    circular["self"] = circular

    with pytest.raises(ValueError, match="Failed to serialize"):
        safe_serialize(circular)


def test_deserialize_invalid_data_raises():
    """Test that invalid deserialization raises ValueError."""
    invalid_json = "{ this is not valid json }"

    with pytest.raises(ValueError, match="Failed to deserialize"):
        safe_deserialize(invalid_json)
