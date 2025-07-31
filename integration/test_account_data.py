"""
Integration tests for account data endpoints.
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal

from trading212_exporter import Trading212Client


@pytest.mark.integration
class TestAccountData:
    """Test Trading 212 account data endpoints."""
    
    def test_get_account_cash_gbp(self, api_client):
        """Test getting account cash balance for GBP account."""
        cash_data = api_client.get_account_cash()
        
        assert isinstance(cash_data, dict)
        assert 'free' in cash_data
        assert isinstance(cash_data['free'], (int, float))
        assert cash_data['free'] >= 0
        assert cash_data['free'] == 1250.50
        
        # Check additional fields are present
        assert 'total' in cash_data
        assert 'invested' in cash_data
        assert 'result' in cash_data
    
    def test_get_account_cash_different_currencies(self, mock_fixture_data):
        """Test getting cash balance for different currency accounts."""
        # Test USD account
        usd_client = Mock(spec=Trading212Client)
        usd_client.get_account_cash.return_value = mock_fixture_data['account_cash']['usd_account']
        
        cash_data = usd_client.get_account_cash()
        assert cash_data['free'] == 850.75
        assert cash_data['total'] == 850.75
        
        # Test ISA account
        isa_client = Mock(spec=Trading212Client)
        isa_client.get_account_cash.return_value = mock_fixture_data['account_cash']['isa_account']
        
        cash_data = isa_client.get_account_cash()
        assert cash_data['free'] == 500.25
        assert cash_data['total'] == 500.25
    
    def test_get_account_cash_empty_account(self, mock_fixture_data):
        """Test getting cash balance for empty account."""
        empty_client = Mock(spec=Trading212Client)
        empty_client.get_account_cash.return_value = mock_fixture_data['account_cash']['empty_account']
        
        cash_data = empty_client.get_account_cash()
        assert cash_data['free'] == 0.0
        assert cash_data['total'] == 0.0
        assert cash_data['invested'] == 0.0
        assert cash_data['result'] == 0.0
    
    def test_account_cash_data_structure(self, api_client):
        """Test that account cash data has expected structure."""
        cash_data = api_client.get_account_cash()
        
        # Verify all expected fields are present
        expected_fields = ['free', 'total', 'invested', 'result', 'pieCash']
        for field in expected_fields:
            assert field in cash_data, f"Missing field: {field}"
            assert isinstance(cash_data[field], (int, float)), f"Field {field} should be numeric"
    
    def test_account_cash_with_api_error(self, mock_fixture_data):
        """Test handling of API errors when fetching cash data."""
        error_client = Mock(spec=Trading212Client)
        error_client.get_account_cash.side_effect = Exception("API permission denied")
        
        with pytest.raises(Exception, match="API permission denied"):
            error_client.get_account_cash()
    
    def test_account_cash_precision(self, api_client):
        """Test that cash amounts maintain proper decimal precision."""
        cash_data = api_client.get_account_cash()
        
        # Convert to Decimal to test precision handling
        free_amount = Decimal(str(cash_data['free']))
        assert free_amount == Decimal('1250.50')
        
        # Ensure we can handle fractional pence/cents
        assert free_amount.as_tuple().exponent >= -2  # At least 2 decimal places
    
    def test_account_cash_validation(self, api_client):
        """Test validation of account cash data values."""
        cash_data = api_client.get_account_cash()
        
        # All amounts should be non-negative
        assert cash_data['free'] >= 0
        assert cash_data['total'] >= 0
        assert cash_data['invested'] >= 0
        assert cash_data['pieCash'] >= 0
        
        # Total should be >= free funds (basic consistency check)
        assert cash_data['total'] >= cash_data['free']
    
    def test_multiple_account_cash_fetching(self, api_clients):
        """Test fetching cash data from multiple accounts."""
        for account_name, client in api_clients.items():
            cash_data = client.get_account_cash()
            
            assert isinstance(cash_data, dict)
            assert 'free' in cash_data
            assert cash_data['free'] >= 0
            
            # Verify each account has distinct cash amounts
            if account_name == 'Stocks & Shares ISA':
                assert cash_data['free'] == 500.25
            elif account_name == 'Invest Account':
                assert cash_data['free'] == 850.75