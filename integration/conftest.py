"""
Shared fixtures for integration tests.
"""

import os
import pytest
from dotenv import load_dotenv

from trading212_exporter import Trading212Client, PortfolioExporter


@pytest.fixture(scope="session")
def api_client():
    """Create a Trading 212 client for integration tests."""
    load_dotenv()
    
    # Check for multiple API keys (new format)
    api_key_isa = os.getenv('API_KEY_STOCKS_ISA')
    api_key_invest = os.getenv('API_KEY_INVEST_ACCOUNT')
    
    # Check for legacy single API key
    api_key_legacy = os.getenv('API_KEY')
    
    # Return the first available API key for backward compatibility with single-client tests
    if api_key_isa:
        return Trading212Client(api_key_isa, account_name='Stocks & Shares ISA')
    elif api_key_invest:
        return Trading212Client(api_key_invest, account_name='Invest Account')
    elif api_key_legacy:
        return Trading212Client(api_key_legacy, account_name='Trading 212')
    else:
        pytest.skip("No API keys found in environment variables")


@pytest.fixture(scope="session")
def api_clients():
    """Create multiple Trading 212 clients for multi-account integration tests."""
    load_dotenv()
    
    # Check for multiple API keys (new format)
    api_key_isa = os.getenv('API_KEY_STOCKS_ISA')
    api_key_invest = os.getenv('API_KEY_INVEST_ACCOUNT')
    
    # Check for legacy single API key
    api_key_legacy = os.getenv('API_KEY')
    
    # Determine which API keys are available
    clients = {}
    
    if api_key_isa:
        clients['Stocks & Shares ISA'] = Trading212Client(api_key_isa, account_name='Stocks & Shares ISA')
    
    if api_key_invest:
        clients['Invest Account'] = Trading212Client(api_key_invest, account_name='Invest Account')
    
    if api_key_legacy and not clients:
        clients['Trading 212'] = Trading212Client(api_key_legacy, account_name='Trading 212')
    
    if not clients:
        pytest.skip("No API keys found in environment variables")
    
    return clients


@pytest.fixture(scope="session")
def portfolio_exporter(api_client):
    """Create a portfolio exporter for single-client integration tests."""
    return PortfolioExporter({'Trading 212': api_client})


@pytest.fixture(scope="session")
def multi_account_exporter(api_clients):
    """Create a portfolio exporter for multi-account integration tests."""
    return PortfolioExporter(api_clients)