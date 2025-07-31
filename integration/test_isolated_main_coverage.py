"""
Isolated integration tests for main module coverage.

These tests target the main CLI entry points to improve coverage.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch
from pathlib import Path

from trading212_exporter import main
from .isolated_base import IsolatedIntegrationTestBase, IsolatedTestData
from .isolated_test_data import SingleAccountTestData


@pytest.mark.integration
class TestIsolatedMainCoverage(IsolatedIntegrationTestBase):
    """Isolated tests for main module functionality."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create test data for main module tests."""
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for main module tests."""
        return "Trading 212"
    
    @patch.dict('os.environ', {'API_KEY': 'test_api_key_12345'})
    def test_isolated_main_function_success(self, tmp_path):
        """Test main function execution with mocked environment."""
        # Change to temp directory
        original_cwd = Path.cwd()
        tmp_path.mkdir(exist_ok=True)
        
        try:
            # Mock the Trading212Client and PortfolioExporter
            with patch('trading212_exporter.main.Trading212Client') as mock_client_class, \
                 patch('trading212_exporter.main.PortfolioExporter') as mock_exporter_class:
                
                # Configure mock client
                mock_client = Mock()
                mock_client.account_name = "Trading 212"
                mock_client_class.return_value = mock_client
                
                # Configure mock exporter
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                
                # Change directory for test
                import os
                os.chdir(tmp_path)
                
                # Call main function
                main.main()
                
                # Verify client was created with correct API key
                mock_client_class.assert_called_once_with('test_api_key_12345', 'Trading 212')
                
                # Verify exporter was created with client
                mock_exporter_class.assert_called_once_with({'Trading 212': mock_client})
                
                # Verify exporter methods were called
                mock_exporter.fetch_data.assert_called_once()
                mock_exporter.save_to_file.assert_called_once()
        
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def test_isolated_main_function_missing_api_key(self, tmp_path, capsys):
        """Test main function with missing API key."""
        # Ensure API_KEY is not in environment
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                main.main()
            
            # Should exit with code 1
            assert exc_info.value.code == 1
            
            # Check error message
            captured = capsys.readouterr()
            assert "API_KEY environment variable not set" in captured.err
    
    @patch.dict('os.environ', {'API_KEY': 'test_api_key_12345'})
    def test_isolated_main_function_with_exception(self, tmp_path, capsys):
        """Test main function handling of exceptions."""
        with patch('trading212_exporter.main.Trading212Client') as mock_client_class:
            # Make client creation raise an exception
            mock_client_class.side_effect = Exception("API connection failed")
            
            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmp_path)
                
                with pytest.raises(SystemExit) as exc_info:
                    main.main()
                
                # Should exit with code 1
                assert exc_info.value.code == 1
                
                # Check error message
                captured = capsys.readouterr()
                assert "Error:" in captured.err
                assert "API connection failed" in captured.err
            
            finally:
                os.chdir(original_cwd)
    
    @patch.dict('os.environ', {'API_KEY': 'test_api_key_12345'})
    def test_isolated_load_env_function(self, tmp_path):
        """Test load_env function."""
        # Create a .env file in temp directory
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=env_file_key_67890\nOTHER_VAR=test_value")
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            
            # Clear environment to test .env loading
            with patch.dict('os.environ', {}, clear=True):
                main.load_env()
                
                # Should load from .env file
                assert os.environ.get('API_KEY') == 'env_file_key_67890'
                assert os.environ.get('OTHER_VAR') == 'test_value'
        
        finally:
            os.chdir(original_cwd)
    
    def test_isolated_load_env_no_file(self, tmp_path):
        """Test load_env function when .env file doesn't exist."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)  # Directory without .env file
            
            # Should not raise exception
            main.load_env()
        
        finally:
            os.chdir(original_cwd)
    
    @patch('sys.argv', ['export_portfolio.py'])
    @patch.dict('os.environ', {'API_KEY': 'test_api_key_12345'})
    def test_isolated_if_name_main_execution(self, tmp_path):
        """Test the if __name__ == '__main__' block."""
        with patch('trading212_exporter.main.main') as mock_main:
            # Import and execute the module as if it was run as script
            import importlib
            
            # This should trigger the if __name__ == '__main__' block
            # We need to reload the module to trigger this
            spec = importlib.util.spec_from_file_location(
                "main_test", 
                Path(__file__).parent.parent / "trading212_exporter" / "main.py"
            )
            module = importlib.util.module_from_spec(spec)
            
            # Mock __name__ to be '__main__'
            module.__name__ = '__main__'
            
            with patch.object(sys, 'argv', ['export_portfolio.py']):
                spec.loader.exec_module(module)
            
            # The main function should have been called
            mock_main.assert_called_once()


@pytest.mark.integration  
class TestIsolatedClientCoverage(IsolatedIntegrationTestBase):
    """Isolated tests to improve client module coverage."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create test data for client tests."""
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for client tests."""
        return "Trading 212"
    
    def test_isolated_client_initialization(self):
        """Test Trading212Client initialization."""
        from trading212_exporter.client import Trading212Client
        
        client = Trading212Client("test_api_key", "Test Account")
        
        assert client.api_key == "test_api_key"
        assert client.account_name == "Test Account"
        assert client.BASE_URL == "https://live.trading212.com/api/v0"
        assert client._request_interval == 0.5
        assert hasattr(client, 'session')
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "test_api_key"
    
    def test_isolated_client_rate_limiting_logic(self):
        """Test rate limiting logic."""
        from trading212_exporter.client import Trading212Client
        import time
        
        client = Trading212Client("test_api_key", "Test Account")
        client._request_interval = 0.1  # Short interval for testing
        
        # First call should not be rate limited
        start_time = time.time()
        client._rate_limit()
        first_call_time = time.time() - start_time
        
        # Should be very fast (no rate limiting)
        assert first_call_time < 0.05
        
        # Second call should be rate limited
        start_time = time.time()
        client._rate_limit()
        second_call_time = time.time() - start_time
        
        # Should be at least the rate limit interval
        assert second_call_time >= client._request_interval * 0.8  # Allow some tolerance
    
    @patch('trading212_exporter.client.requests.Session.request')
    def test_isolated_client_make_request_success(self, mock_request):
        """Test successful request handling."""
        from trading212_exporter.client import Trading212Client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        client = Trading212Client("test_api_key", "Test Account")
        result = client._make_request("/test/endpoint")
        
        assert result == {"test": "data"}
        mock_request.assert_called_once()
        
        # Verify correct URL construction
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://live.trading212.com/api/v0/test/endpoint"
    
    @patch('trading212_exporter.client.requests.Session.request')
    def test_isolated_client_make_request_rate_limit_retry(self, mock_request):
        """Test rate limit retry logic."""
        from trading212_exporter.client import Trading212Client
        import requests
        
        # Mock rate limit response then success
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        
        success_response = Mock()
        success_response.json.return_value = {"success": True}
        success_response.raise_for_status.return_value = None
        
        mock_request.side_effect = [
            requests.exceptions.HTTPError("429 Too Many Requests"),  # First call fails
            success_response  # Second call succeeds
        ]
        mock_request.side_effect[0].response = rate_limit_response
        
        client = Trading212Client("test_api_key", "Test Account")
        
        # Should handle rate limit and retry
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = client._make_request("/test/endpoint")
        
        assert result == {"success": True}
        assert mock_request.call_count == 2  # Should have retried