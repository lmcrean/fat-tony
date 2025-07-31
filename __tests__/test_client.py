"""
Unit tests for Trading212Client class.
"""

import pytest
import time
from unittest.mock import Mock, patch
import requests
import responses

from trading212_exporter import Trading212Client


class TestTrading212Client:
    """Unit tests for Trading212Client."""
    
    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        return Trading212Client("test-api-key")
    
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test-api-key"
        assert client.BASE_URL == "https://live.trading212.com/api/v0"
        assert client.session.headers["Authorization"] == "test-api-key"
        assert client.session.headers["Content-Type"] == "application/json"
        assert client._request_interval == 0.5
    
    def test_rate_limiting(self, client):
        """Test rate limiting mechanism."""
        start_time = time.time()
        
        # First call should not be delayed
        client._rate_limit()
        first_call_time = time.time() - start_time
        
        # Second call should be delayed
        client._rate_limit()
        second_call_time = time.time() - start_time
        
        # Should respect the rate limit interval
        assert second_call_time >= client._request_interval
    
    @responses.activate
    def test_make_request_success(self, client):
        """Test successful API request."""
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/test",
            json={"status": "success"},
            status=200
        )
        
        result = client._make_request("/test")
        assert result == {"status": "success"}
    
    @responses.activate
    def test_make_request_404_error(self, client):
        """Test handling of 404 error."""
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/test",
            status=404
        )
        
        with pytest.raises(requests.exceptions.HTTPError):
            client._make_request("/test")
    
    @responses.activate
    def test_make_request_401_authentication_error(self, client):
        """Test handling of authentication error."""
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/test",
            status=401
        )
        
        with pytest.raises(SystemExit):
            client._make_request("/test")
    
    @responses.activate
    def test_make_request_rate_limit_retry(self, client):
        """Test automatic retry on rate limit."""
        # First call returns 429, second call succeeds
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/test",
            status=429
        )
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/test",
            json={"status": "success"},
            status=200
        )
        
        with patch('time.sleep') as mock_sleep:
            result = client._make_request("/test")
            assert result == {"status": "success"}
            mock_sleep.assert_called_once_with(5)
    
    @responses.activate
    def test_get_portfolio(self, client):
        """Test get_portfolio method."""
        mock_portfolio = [
            {
                "ticker": "AAPL",
                "quantity": 10,
                "averagePrice": 150.0,
                "currentPrice": 160.0
            }
        ]
        
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/equity/portfolio",
            json=mock_portfolio,
            status=200
        )
        
        result = client.get_portfolio()
        assert result == mock_portfolio
    
    @responses.activate
    def test_get_position_details(self, client):
        """Test get_position_details method."""
        mock_details = {
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "currency": "USD"
        }
        
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/equity/portfolio/AAPL",
            json=mock_details,
            status=200
        )
        
        result = client.get_position_details("AAPL")
        assert result == mock_details
    
    @responses.activate
    def test_get_account_cash(self, client):
        """Test get_account_cash method."""
        mock_cash = {
            "free": 1000.0,
            "total": 6000.0,
            "currency": "GBP"
        }
        
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/account/cash",
            json=mock_cash,
            status=200
        )
        
        result = client.get_account_cash()
        assert result == mock_cash
    
    @responses.activate
    def test_get_account_metadata(self, client):
        """Test get_account_metadata method."""
        mock_metadata = {
            "currencyCode": "GBP",
            "id": 12345
        }
        
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/account/metadata",
            json=mock_metadata,
            status=200
        )
        
        result = client.get_account_metadata()
        assert result == mock_metadata
    
    @responses.activate
    def test_network_error_handling(self, client):
        """Test handling of network errors."""
        responses.add(
            responses.GET,
            "https://live.trading212.com/api/v0/test",
            body=requests.exceptions.ConnectionError("Network error")
        )
        
        with pytest.raises(requests.exceptions.ConnectionError):
            client._make_request("/test")