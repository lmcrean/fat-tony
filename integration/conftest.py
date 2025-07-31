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
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        pytest.skip("API_KEY not found in environment variables")
    
    return Trading212Client(api_key)


@pytest.fixture(scope="session")
def portfolio_exporter(api_client):
    """Create a portfolio exporter for integration tests."""
    return PortfolioExporter(api_client)