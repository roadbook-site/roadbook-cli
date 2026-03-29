import pytest
from roadbook.core.config import _merge_config

def test_merge_config_simple():
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    result = _merge_config(base, override)
    assert result == {"a": 1, "b": 3, "c": 4}

def test_merge_config_nested():
    base = {
        "core": {"url": "http://localhost", "timeout": 30},
        "other": 1
    }
    override = {
        "core": {"timeout": 60, "new_key": "value"}
    }
    result = _merge_config(base, override)
    assert result == {
        "core": {"url": "http://localhost", "timeout": 60, "new_key": "value"},
        "other": 1
    }

def test_merge_config_empty():
    base = {"a": 1}
    override = {}
    assert _merge_config(base, override) == {"a": 1}
    
    base2 = {}
    override2 = {"a": 1}
    assert _merge_config(base2, override2) == {"a": 1}
