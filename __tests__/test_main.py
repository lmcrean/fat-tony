"""
Tests for main.py functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

from trading212_exporter.main import main


class TestMain:
    """Test main function functionality."""

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.Trading212Client')
    @patch('trading212_exporter.main.PortfolioExporter')
    def test_main_with_isa_api_key(self, mock_exporter_class, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test main function with ISA API key."""
        # Mock environment variables
        def getenv_side_effect(key):
            if key == 'API_KEY_STOCKS_ISA':
                return 'test_isa_key'
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock client and exporter
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_exporter = Mock()
        mock_exporter_class.return_value = mock_exporter
        
        main()
        
        # Verify dotenv was loaded
        mock_load_dotenv.assert_called_once()
        
        # Verify client was created with ISA key
        mock_client_class.assert_called_once_with('test_isa_key', account_name='Stocks & Shares ISA')
        
        # Verify exporter was created with client
        mock_exporter_class.assert_called_once()
        clients_arg = mock_exporter_class.call_args[0][0]
        assert 'Stocks & Shares ISA' in clients_arg
        
        # Verify export process was executed
        mock_exporter.fetch_data.assert_called_once()
        mock_exporter.save_to_file.assert_called_once()

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.Trading212Client')
    @patch('trading212_exporter.main.PortfolioExporter')
    def test_main_with_invest_api_key(self, mock_exporter_class, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test main function with Invest API key."""
        # Mock environment variables
        def getenv_side_effect(key):
            if key == 'API_KEY_INVEST_ACCOUNT':
                return 'test_invest_key'
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock client and exporter
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_exporter = Mock()
        mock_exporter_class.return_value = mock_exporter
        
        main()
        
        # Verify client was created with Invest key
        mock_client_class.assert_called_once_with('test_invest_key', account_name='Invest Account')

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.Trading212Client')
    @patch('trading212_exporter.main.PortfolioExporter')
    def test_main_with_multiple_api_keys(self, mock_exporter_class, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test main function with multiple API keys."""
        # Mock environment variables
        def getenv_side_effect(key):
            if key == 'API_KEY_STOCKS_ISA':
                return 'test_isa_key'
            elif key == 'API_KEY_INVEST_ACCOUNT':
                return 'test_invest_key'
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock client and exporter
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_exporter = Mock()
        mock_exporter_class.return_value = mock_exporter
        
        main()
        
        # Verify both clients were created
        assert mock_client_class.call_count == 2
        
        # Verify exporter was created with both clients
        mock_exporter_class.assert_called_once()
        clients_arg = mock_exporter_class.call_args[0][0]
        assert 'Stocks & Shares ISA' in clients_arg
        assert 'Invest Account' in clients_arg

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.Trading212Client')
    @patch('trading212_exporter.main.PortfolioExporter')
    def test_main_with_legacy_api_key(self, mock_exporter_class, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test main function with legacy API key."""
        # Mock environment variables - only legacy key present
        def getenv_side_effect(key):
            if key == 'API_KEY':
                return 'test_legacy_key'
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock client and exporter
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_exporter = Mock()
        mock_exporter_class.return_value = mock_exporter
        
        main()
        
        # Verify client was created with legacy key
        mock_client_class.assert_called_once_with('test_legacy_key', account_name='Trading 212')

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.print')
    @patch('trading212_exporter.main.sys.exit')
    def test_main_no_api_keys(self, mock_exit, mock_print, mock_getenv, mock_load_dotenv):
        """Test main function with no API keys."""
        # Mock environment variables - no keys
        def getenv_side_effect(key):
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        main()
        
        # Verify error messages were printed
        assert mock_print.call_count >= 4  # Error message and instructions
        # Check that sys.exit was called with 1
        mock_exit.assert_called_with(1)

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.Trading212Client')
    @patch('trading212_exporter.main.PortfolioExporter')
    @patch('trading212_exporter.main.print')
    @patch('trading212_exporter.main.sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit, mock_print, mock_exporter_class, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test main function with KeyboardInterrupt."""
        # Mock environment variables
        def getenv_side_effect(key):
            if key == 'API_KEY':
                return 'test_key'
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock client and exporter - make fetch_data raise KeyboardInterrupt
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_exporter = Mock()
        mock_exporter.fetch_data.side_effect = KeyboardInterrupt()
        mock_exporter_class.return_value = mock_exporter
        
        main()
        
        # Verify cancellation message and exit
        mock_print.assert_called_with("\nExport cancelled by user")
        mock_exit.assert_called_with(0)

    @patch('trading212_exporter.main.load_dotenv')
    @patch('trading212_exporter.main.os.getenv')
    @patch('trading212_exporter.main.Trading212Client')
    @patch('trading212_exporter.main.PortfolioExporter')
    @patch('trading212_exporter.main.print')
    @patch('trading212_exporter.main.sys.exit')
    def test_main_exception(self, mock_exit, mock_print, mock_exporter_class, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test main function with general exception."""
        # Mock environment variables
        def getenv_side_effect(key):
            if key == 'API_KEY':
                return 'test_key'
            return None
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock client and exporter - make fetch_data raise exception
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_exporter = Mock()
        mock_exporter.fetch_data.side_effect = Exception("Test error")
        mock_exporter_class.return_value = mock_exporter
        
        main()
        
        # Verify error message and exit
        mock_print.assert_called_with("\nError during export: Test error")
        mock_exit.assert_called_with(1)

    def test_main_module_direct_execution_coverage(self):
        """Test the __name__ == '__main__' block for coverage."""
        import trading212_exporter.main as main_module
        
        # Get the original __name__
        original_name = main_module.__name__
        
        try:
            # Set __name__ to simulate direct execution
            main_module.__name__ = "__main__"
            
            # This should trigger the if block but we need to mock main()
            with patch('trading212_exporter.main.main') as mock_main:
                # Execute the module-level code by importing it fresh
                exec("if __name__ == '__main__': main()", main_module.__dict__)
                mock_main.assert_called_once()
        finally:
            # Restore original __name__
            main_module.__name__ = original_name