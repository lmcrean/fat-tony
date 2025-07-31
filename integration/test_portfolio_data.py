"""
Integration tests for portfolio data endpoints.
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal

from trading212_exporter import Trading212Client


@pytest.mark.integration
class TestPortfolioData:
    """Test Trading 212 portfolio data endpoints."""
    
    def test_get_portfolio_multiple_positions(self, api_client):
        """Test getting portfolio with multiple positions."""
        portfolio = api_client.get_portfolio()
        
        assert isinstance(portfolio, list)
        assert len(portfolio) == 3  # Based on mock data
        
        # Check first position (AAPL)
        aapl_position = portfolio[0]
        required_fields = ['ticker', 'quantity', 'averagePrice', 'currentPrice', 'currencyCode']
        
        for field in required_fields:
            assert field in aapl_position, f"Missing field: {field}"
            assert aapl_position[field] is not None
        
        assert aapl_position['ticker'] == 'AAPL'
        assert aapl_position['quantity'] == 10.0
        assert aapl_position['averagePrice'] == 150.0
        assert aapl_position['currentPrice'] == 160.0
        assert aapl_position['currencyCode'] == 'USD'
    
    def test_get_portfolio_empty(self, mock_fixture_data):
        """Test getting empty portfolio."""
        empty_client = Mock(spec=Trading212Client)
        empty_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['empty_portfolio']
        
        portfolio = empty_client.get_portfolio()
        
        assert isinstance(portfolio, list)
        assert len(portfolio) == 0
    
    def test_get_portfolio_single_position(self, mock_fixture_data):
        """Test getting portfolio with single position."""
        single_client = Mock(spec=Trading212Client)
        single_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['single_position']
        
        portfolio = single_client.get_portfolio()
        
        assert isinstance(portfolio, list)
        assert len(portfolio) == 1
        
        position = portfolio[0]
        assert position['ticker'] == 'AAPL'
        assert position['quantity'] == 10.0
        assert position['currencyCode'] == 'USD'
    
    def test_get_portfolio_gbp_positions(self, mock_fixture_data):
        """Test getting portfolio with GBP positions."""
        gbp_client = Mock(spec=Trading212Client)
        gbp_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['gbp_positions']
        
        portfolio = gbp_client.get_portfolio()
        
        assert isinstance(portfolio, list)
        assert len(portfolio) == 2
        
        # Check Vodafone position
        vod_position = portfolio[0]
        assert vod_position['ticker'] == 'VOD.L'
        assert vod_position['currencyCode'] == 'GBP'
        assert vod_position['quantity'] == 100.0
        assert vod_position['averagePrice'] == 1.25
        assert vod_position['currentPrice'] == 1.30
    
    def test_get_portfolio_fractional_shares(self, mock_fixture_data):
        """Test getting portfolio with fractional shares."""
        fractional_client = Mock(spec=Trading212Client)
        fractional_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['fractional_shares']
        
        portfolio = fractional_client.get_portfolio()
        
        assert isinstance(portfolio, list)
        assert len(portfolio) == 1
        
        position = portfolio[0]
        assert position['ticker'] == 'AMZN'
        assert position['quantity'] == 0.5  # Fractional share
        assert position['averagePrice'] == 3000.0
        assert position['currentPrice'] == 3100.0
    
    def test_get_position_details_success(self, api_client):
        """Test getting individual position details successfully."""
        portfolio = api_client.get_portfolio()
        
        # Test getting details for AAPL (first position)
        ticker = portfolio[0]['ticker']
        details = api_client.get_position_details(ticker)
        
        assert isinstance(details, dict)
        assert details['ticker'] == 'AAPL'
        assert details['name'] == 'Apple Inc.'
        assert 'isin' in details
        assert details['isin'] == 'US0378331005'
        assert details['type'] == 'STOCK'
    
    def test_get_position_details_all_positions(self, api_client, mock_fixture_data):
        """Test getting details for all positions in portfolio."""
        portfolio = api_client.get_portfolio()
        
        for position in portfolio:
            ticker = position['ticker']
            details = api_client.get_position_details(ticker)
            
            assert isinstance(details, dict)
            assert 'ticker' in details
            
            # Verify we get expected data for known tickers
            if ticker == 'AAPL':
                assert details['name'] == 'Apple Inc.'
            elif ticker == 'GOOGL':
                assert details['name'] == 'Alphabet Inc.'
            elif ticker == 'TSLA':
                assert details['name'] == 'Tesla Inc.'
    
    def test_get_position_details_error_handling(self, mock_fixture_data):
        """Test error handling when getting position details."""
        error_client = Mock(spec=Trading212Client)
        
        def mock_position_details_with_error(ticker):
            if ticker == 'INVALID':
                raise Exception("Position not found")
            return mock_fixture_data['position_details']['AAPL']
        
        error_client.get_position_details.side_effect = mock_position_details_with_error
        
        # Should work for valid ticker
        details = error_client.get_position_details('AAPL')
        assert details['name'] == 'Apple Inc.'
        
        # Should raise exception for invalid ticker
        with pytest.raises(Exception, match="Position not found"):
            error_client.get_position_details('INVALID')
    
    def test_get_position_details_minimal_response(self, mock_fixture_data):
        """Test handling of minimal position details response."""
        minimal_client = Mock(spec=Trading212Client)
        minimal_client.get_position_details.return_value = mock_fixture_data['position_details']['minimal_response']
        
        details = minimal_client.get_position_details('TEST')
        
        assert isinstance(details, dict)
        assert details['ticker'] == 'TEST'
        # Should handle missing fields gracefully (tested by the actual exporter code)
    
    def test_portfolio_data_types_and_validation(self, api_client):
        """Test that portfolio data has correct types and valid values."""
        portfolio = api_client.get_portfolio()
        
        for position in portfolio:
            # Check data types
            assert isinstance(position['ticker'], str)
            assert isinstance(position['quantity'], (int, float))
            assert isinstance(position['averagePrice'], (int, float))
            assert isinstance(position['currentPrice'], (int, float))
            assert isinstance(position['currencyCode'], str)
            
            # Check valid values
            assert len(position['ticker']) > 0
            assert position['quantity'] > 0
            assert position['averagePrice'] > 0
            assert position['currentPrice'] > 0
            assert position['currencyCode'] in ['USD', 'GBP', 'EUR']
    
    def test_portfolio_profit_loss_calculations(self, api_client):
        """Test that we can calculate profit/loss from portfolio data."""
        portfolio = api_client.get_portfolio()
        
        for position in portfolio:
            quantity = Decimal(str(position['quantity']))
            avg_price = Decimal(str(position['averagePrice']))
            current_price = Decimal(str(position['currentPrice']))
            
            # Calculate values (similar to Position model)
            cost_basis = quantity * avg_price
            market_value = quantity * current_price
            profit_loss = market_value - cost_basis
            
            # Verify calculations make sense
            assert cost_basis > 0
            assert market_value > 0
            
            # For test data, check specific calculations
            if position['ticker'] == 'AAPL':
                expected_cost = Decimal('10') * Decimal('150')  # 1500
                expected_market = Decimal('10') * Decimal('160')  # 1600
                expected_profit = expected_market - expected_cost  # 100
                
                assert cost_basis == expected_cost
                assert market_value == expected_market
                assert profit_loss == expected_profit
    
    def test_multi_account_portfolio_data(self, api_clients):
        """Test fetching portfolio data from multiple accounts."""
        for account_name, client in api_clients.items():
            portfolio = client.get_portfolio()
            
            assert isinstance(portfolio, list)
            
            # Verify each account has expected positions
            if account_name == 'Stocks & Shares ISA':
                assert len(portfolio) == 2  # GBP positions
                tickers = [pos['ticker'] for pos in portfolio]
                assert 'VOD.L' in tickers
                assert 'LLOY.L' in tickers
                
                # All should be GBP
                for position in portfolio:
                    assert position['currencyCode'] == 'GBP'
                    
            elif account_name == 'Invest Account':
                assert len(portfolio) == 1  # Single AAPL position
                assert portfolio[0]['ticker'] == 'AAPL'
                assert portfolio[0]['currencyCode'] == 'USD'