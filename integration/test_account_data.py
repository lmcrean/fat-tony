"""
Integration tests for account data endpoints.
"""

import pytest


@pytest.mark.integration
class TestAccountData:
    """Test Trading 212 account data endpoints."""
    
    def test_get_account_cash(self, api_client):
        """Test getting account cash balance."""
        cash_data = api_client.get_account_cash()
        
        assert isinstance(cash_data, dict)
        assert 'free' in cash_data
        assert isinstance(cash_data['free'], (int, float))
        assert cash_data['free'] >= 0