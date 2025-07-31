"""
Shared fixtures for integration tests.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from trading212_exporter import Trading212Client, PortfolioExporter


# Helper function to load fixture data
def load_fixture(filename):
    """Load JSON fixture data from the fixtures directory."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / filename, 'r') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_fixture_data():
    """Load all fixture data for tests."""
    return {
        'account_metadata': load_fixture('account_metadata.json'),
        'account_cash': load_fixture('account_cash.json'),
        'portfolio_positions': load_fixture('portfolio_positions.json'),
        'position_details': load_fixture('position_details.json'),
        'api_errors': load_fixture('api_errors.json')
    }


@pytest.fixture
def mock_api_client(mock_fixture_data):
    """Create a mocked Trading 212 client for integration tests."""
    client = Mock(spec=Trading212Client)
    client.account_name = 'Trading 212'
    client._request_interval = 5  # For rate limiting tests
    
    # Mock successful API responses - use USD account to match USD positions
    client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['usd_account']
    client.get_account_cash.return_value = mock_fixture_data['account_cash']['usd_account']
    client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['multiple_positions']
    
    # Mock position details with dynamic responses
    def mock_position_details(ticker):
        details = mock_fixture_data['position_details'].get(ticker)
        if details and 'error' not in details:
            return details
        elif ticker == 'INVALID':
            raise Exception("Position not found")
        else:
            return mock_fixture_data['position_details']['minimal_response']
    
    client.get_position_details.side_effect = mock_position_details
    
    return client


@pytest.fixture
def mock_api_clients(mock_fixture_data):
    """Create multiple mocked Trading 212 clients for multi-account integration tests."""
    # ISA Account Client
    isa_client = Mock(spec=Trading212Client)
    isa_client.account_name = 'Stocks & Shares ISA'
    isa_client._request_interval = 5
    isa_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['isa_account']
    isa_client.get_account_cash.return_value = mock_fixture_data['account_cash']['isa_account']
    isa_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['gbp_positions']
    
    def isa_position_details(ticker):
        return mock_fixture_data['position_details'].get(ticker, {'ticker': ticker})
    isa_client.get_position_details.side_effect = isa_position_details
    
    # Invest Account Client  
    invest_client = Mock(spec=Trading212Client)
    invest_client.account_name = 'Invest Account'
    invest_client._request_interval = 5
    invest_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['usd_account']
    invest_client.get_account_cash.return_value = mock_fixture_data['account_cash']['usd_account']
    invest_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['single_position']
    
    def invest_position_details(ticker):
        return mock_fixture_data['position_details'].get(ticker, {'ticker': ticker})
    invest_client.get_position_details.side_effect = invest_position_details
    
    return {
        'Stocks & Shares ISA': isa_client,
        'Invest Account': invest_client
    }


@pytest.fixture
def api_client(mock_api_client):
    """Create a Trading 212 client for integration tests (mocked by default)."""
    return mock_api_client


@pytest.fixture
def api_clients(mock_api_clients):
    """Create multiple Trading 212 clients for multi-account integration tests (mocked by default)."""
    return mock_api_clients


@pytest.fixture
def portfolio_exporter(api_client):
    """Create a portfolio exporter for single-client integration tests."""
    return PortfolioExporter({'Trading 212': api_client})


@pytest.fixture
def multi_account_exporter(api_clients):
    """Create a portfolio exporter for multi-account integration tests."""
    return PortfolioExporter(api_clients)


# Helper fixtures for specific test scenarios
@pytest.fixture
def empty_portfolio_client(mock_fixture_data):
    """Create a client with empty portfolio for testing edge cases."""
    client = Mock(spec=Trading212Client)
    client.account_name = 'Trading 212'
    client._request_interval = 5
    client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['success']
    client.get_account_cash.return_value = mock_fixture_data['account_cash']['empty_account']
    client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['empty_portfolio']
    return client


@pytest.fixture
def error_prone_client(mock_fixture_data):
    """Create a client that throws various API errors for testing error handling."""
    client = Mock(spec=Trading212Client)
    client.account_name = 'Trading 212'
    client._request_interval = 5
    
    # Make metadata call fail with permission denied
    client.get_account_metadata.side_effect = Exception("API permission denied")
    
    # Make cash call fail
    client.get_account_cash.side_effect = Exception("API permission denied")
    
    # Return valid portfolio but fail on position details
    client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['single_position']
    client.get_position_details.side_effect = Exception("API Error")
    
    return client


@pytest.fixture
def rate_limited_client(mock_fixture_data):
    """Create a client for testing rate limiting behavior."""
    client = Mock(spec=Trading212Client)  
    client.account_name = 'Trading 212'
    client._request_interval = 2  # Shorter interval for faster tests
    
    # Track call times for rate limiting verification
    client._last_request_time = 0
    
    def mock_rate_limited_call(*args, **kwargs):
        import time
        current_time = time.time()
        if client._last_request_time > 0:
            time_diff = current_time - client._last_request_time
            if time_diff < client._request_interval:
                time.sleep(client._request_interval - time_diff)
        client._last_request_time = time.time()
        return mock_fixture_data['account_metadata']['success']
    
    client.get_account_metadata.side_effect = mock_rate_limited_call
    client.get_account_cash.side_effect = mock_rate_limited_call
    
    return client