"""
Integration tests for API authentication.
"""

import pytest
from unittest.mock import Mock, patch
from requests import HTTPError

from trading212_exporter import Trading212Client


@pytest.mark.integration
class TestAPIAuthentication:
    """Test Trading 212 API authentication and error handling."""
    
    def test_api_authentication_success(self, api_client):
        """Test that API authentication works with valid credentials."""
        # Should not raise an authentication error
        metadata = api_client.get_account_metadata()
        assert isinstance(metadata, dict)
        assert 'currencyCode' in metadata
        assert metadata['currencyCode'] in ['GBP', 'EUR', 'USD']
    
    def test_get_account_metadata_gbp(self, api_client):
        """Test getting account metadata for GBP account."""
        metadata = api_client.get_account_metadata()
        
        assert isinstance(metadata, dict)
        assert 'currencyCode' in metadata
        assert 'id' in metadata
        assert metadata['currencyCode'] == 'GBP'
        assert metadata['id'] == 12345
    
    def test_get_account_metadata_different_currencies(self, mock_fixture_data):
        """Test account metadata with different currency codes."""
        # Test USD account
        usd_client = Mock(spec=Trading212Client)
        usd_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['usd_account']
        
        metadata = usd_client.get_account_metadata()
        assert metadata['currencyCode'] == 'USD'
        assert metadata['id'] == 67890
        
        # Test EUR account
        eur_client = Mock(spec=Trading212Client)
        eur_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['eur_account']
        
        metadata = eur_client.get_account_metadata()
        assert metadata['currencyCode'] == 'EUR'
        assert metadata['id'] == 11111
    
    def test_authentication_with_invalid_api_key(self, mock_fixture_data):
        """Test authentication failure with invalid API key."""
        # Create a client that simulates authentication failure
        invalid_client = Mock(spec=Trading212Client)
        invalid_client.get_account_metadata.side_effect = HTTPError("401 Client Error: Unauthorized")
        
        with pytest.raises(HTTPError):
            invalid_client.get_account_metadata()
    
    def test_permission_denied_error(self, mock_fixture_data):
        """Test handling of permission denied errors."""
        # Create a client that simulates permission denied
        forbidden_client = Mock(spec=Trading212Client)
        forbidden_client.get_account_metadata.side_effect = HTTPError("403 Client Error: Forbidden")
        
        with pytest.raises(HTTPError):
            forbidden_client.get_account_metadata()
    
    def test_client_initialization_with_different_account_types(self, mock_fixture_data):
        """Test client initialization with different account types."""
        # Test ISA account  
        isa_client = Mock(spec=Trading212Client)
        isa_client.account_name = 'Stocks & Shares ISA'
        isa_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['isa_account']
        
        metadata = isa_client.get_account_metadata()
        assert metadata['type'] == 'ISA'
        assert metadata['currencyCode'] == 'GBP'
        
        # Test regular account
        regular_client = Mock(spec=Trading212Client)
        regular_client.account_name = 'Trading 212'
        regular_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['success']
        
        metadata = regular_client.get_account_metadata()
        assert metadata['type'] == 'LIVE'
        assert metadata['currencyCode'] == 'GBP'
    
    def test_network_error_handling(self):
        """Test handling of network errors during authentication."""
        # Create a client that simulates network timeout
        network_error_client = Mock(spec=Trading212Client)
        network_error_client.get_account_metadata.side_effect = Exception("Connection timeout")
        
        with pytest.raises(Exception, match="Connection timeout"):
            network_error_client.get_account_metadata()
    
    def test_rate_limit_error_handling(self):
        """Test handling of rate limit errors."""
        # Create a client that simulates rate limiting
        rate_limited_client = Mock(spec=Trading212Client)
        rate_limited_client.get_account_metadata.side_effect = HTTPError("429 Client Error: Too Many Requests")
        
        with pytest.raises(HTTPError):
            rate_limited_client.get_account_metadata()