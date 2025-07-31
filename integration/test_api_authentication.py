"""
Integration tests for API authentication.
"""

import pytest


@pytest.mark.integration
class TestAPIAuthentication:
    """Test Trading 212 API authentication."""
    
    def test_api_authentication(self, api_client):
        """Test that API authentication works."""
        # This should not raise an authentication error
        try:
            metadata = api_client.get_account_metadata()
            assert isinstance(metadata, dict)
            assert 'currencyCode' in metadata
        except Exception as e:
            pytest.fail(f"Authentication failed: {e}")
    
    def test_get_account_metadata(self, api_client):
        """Test getting account metadata."""
        metadata = api_client.get_account_metadata()
        
        assert isinstance(metadata, dict)
        assert 'currencyCode' in metadata
        assert metadata['currencyCode'] in ['GBP', 'EUR', 'USD']