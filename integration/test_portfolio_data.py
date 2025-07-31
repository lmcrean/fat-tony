"""
Integration tests for portfolio data endpoints.
"""

import pytest


@pytest.mark.integration
class TestPortfolioData:
    """Test Trading 212 portfolio data endpoints."""
    
    def test_get_portfolio(self, api_client):
        """Test getting portfolio positions."""
        portfolio = api_client.get_portfolio()
        
        assert isinstance(portfolio, list)
        
        if portfolio:  # If there are positions
            position = portfolio[0]
            required_fields = ['ticker', 'quantity', 'averagePrice', 'currentPrice']
            
            for field in required_fields:
                assert field in position, f"Missing field: {field}"
                assert position[field] is not None
    
    def test_get_position_details(self, api_client):
        """Test getting individual position details."""
        portfolio = api_client.get_portfolio()
        
        if not portfolio:
            pytest.skip("No positions in portfolio to test")
        
        ticker = portfolio[0]['ticker']
        details = api_client.get_position_details(ticker)
        
        assert isinstance(details, dict)
        # Check for common fields that should exist in position details
        common_fields = ['ticker', 'averagePrice', 'currentPrice', 'quantity']
        found_fields = [field for field in common_fields if field in details]
        assert len(found_fields) > 0, f"Expected at least one common field, got: {list(details.keys())}"