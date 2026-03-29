import pytest
from unittest.mock import patch
import os
from roadbook.core.i18n import get_system_language, get_language, t

def test_get_system_language_env():
    with patch.dict(os.environ, {'LANG': 'zh_CN.UTF-8'}, clear=True):
        assert get_system_language() == 'zh'
        
    with patch.dict(os.environ, {'LANG': 'en_US.UTF-8'}, clear=True):
        assert get_system_language() == 'en'

@patch('roadbook.core.i18n.load_config')
def test_get_language_from_config(mock_load_config):
    mock_load_config.return_value = {"core": {"language": "zh"}}
    assert get_language() == "zh"

    mock_load_config.return_value = {"core": {"language": "en"}}
    assert get_language() == "en"

@patch('roadbook.core.i18n.get_language')
def test_translation(mock_get_language):
    mock_get_language.return_value = "en"
    assert t("init_success", name="test", rb_id="123") == "Successfully initialized roadbook scaffold for 'test' (ID: 123)"
    
    mock_get_language.return_value = "zh"
    assert t("init_success", name="test", rb_id="123") == "成功为 'test' 初始化路书脚手架 (ID: 123)"

def test_translation_fallback():
    # When a key doesn't exist, it should return the key itself
    assert t("non_existent_key") == "non_existent_key"
