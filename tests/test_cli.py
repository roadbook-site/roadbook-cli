import pytest
from unittest.mock import patch, MagicMock
import sys
from roadbook.cli import main

def test_cli_help(capsys):
    """Test the --help command"""
    with patch.object(sys, 'argv', ['roadbook', '--help']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
    
    captured = capsys.readouterr()
    assert "AI-Agent Roadbook CLI" in captured.out
    assert "Command Categories:" in captured.out

def test_cli_version(capsys):
    """Test the --version command"""
    with patch.object(sys, 'argv', ['roadbook', '--version']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0

@patch('roadbook.cli.library.list_books')
def test_cli_list(mock_list_books):
    """Test the list command"""
    with patch.object(sys, 'argv', ['roadbook', 'list']):
        main()
        mock_list_books.assert_called_once()

@patch('roadbook.cli.search.search_books')
def test_cli_search(mock_search_books):
    """Test the search command"""
    with patch.object(sys, 'argv', ['roadbook', 'search', 'test_keyword']):
        main()
        mock_search_books.assert_called_once()

@patch('roadbook.cli.executor.run_book')
def test_cli_run(mock_run_book):
    """Test the run command"""
    with patch.object(sys, 'argv', ['roadbook', 'run', 'book_id', '--inputs', '{"key": "value"}']):
        main()
        mock_run_book.assert_called_once()

@patch('roadbook.cli.run.run_history')
def test_cli_logs_list(mock_run_history):
    """Test the logs list command"""
    with patch.object(sys, 'argv', ['roadbook', 'logs', 'list', 'book_id']):
        main()
        mock_run_history.assert_called_once()

@patch('roadbook.cli.initialize.init_book')
def test_cli_init(mock_init_book):
    """Test the init command"""
    with patch.object(sys, 'argv', ['roadbook', 'init', 'my_book', '--description', 'test desc']):
        main()
        mock_init_book.assert_called_once()

@patch('roadbook.cli.doctor.run_doctor')
def test_cli_doctor(mock_run_doctor):
    """Test the doctor command"""
    with patch.object(sys, 'argv', ['roadbook', 'doctor']):
        main()
        mock_run_doctor.assert_called_once()

@patch('roadbook.cli.config.config_get')
def test_cli_config_get(mock_config_get):
    """Test the config get command"""
    with patch.object(sys, 'argv', ['roadbook', 'config', 'get', 'browser.headless']):
        main()
        mock_config_get.assert_called_once()

@patch('roadbook.cli.browser.browser_main')
def test_cli_browser(mock_browser_main):
    """Test the browser command"""
    with patch.object(sys, 'argv', ['roadbook', 'browser']):
        main()
        mock_browser_main.assert_called_once()

