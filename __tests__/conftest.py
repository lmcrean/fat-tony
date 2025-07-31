"""
Pytest configuration and shared fixtures.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from trading212_exporter import Position, AccountSummary, Trading212Client


@pytest.fixture
def mock_api_responses():
    """Mock API responses for testing."""
    return {
        'metadata': {
            'currencyCode': 'GBP',
            'id': 12345
        },
        'portfolio': [
            {
                'ticker': 'AAPL',
                'quantity': 10.0,
                'averagePrice': 150.0,
                'currentPrice': 160.0,
                'currencyCode': 'USD'
            },
            {
                'ticker': 'GOOGL',
                'quantity': 5.0,
                'averagePrice': 2000.0,
                'currentPrice': 1900.0,
                'currencyCode': 'USD'
            },
            {
                'ticker': 'TSLA',
                'quantity': 2.5,
                'averagePrice': 800.0,
                'currentPrice': 850.0,
                'currencyCode': 'USD'
            }
        ],
        'position_details': {
            'AAPL': {
                'name': 'Apple Inc.',
                'ticker': 'AAPL',
                'currency': 'USD'
            },
            'GOOGL': {
                'name': 'Alphabet Inc. Class A',
                'ticker': 'GOOGL',
                'currency': 'USD'
            },
            'TSLA': {
                'name': 'Tesla, Inc.',
                'ticker': 'TSLA',
                'currency': 'USD'
            }
        },
        'cash': {
            'free': 2500.0,
            'total': 15000.0,
            'currency': 'GBP'
        }
    }


@pytest.fixture
def sample_positions():
    """Sample positions for testing."""
    return [
        Position(
            ticker="AAPL",
            name="Apple Inc.",
            shares=Decimal("10.0"),
            average_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
            currency="USD"
        ),
        Position(
            ticker="GOOGL",
            name="Alphabet Inc. Class A",
            shares=Decimal("5.0"),
            average_price=Decimal("2000.00"),
            current_price=Decimal("1900.00"),
            currency="USD"
        ),
        Position(
            ticker="TSLA",
            name="Tesla, Inc.",
            shares=Decimal("2.5"),
            average_price=Decimal("800.00"),
            current_price=Decimal("850.00"),
            currency="USD"
        )
    ]


@pytest.fixture
def sample_account_summary():
    """Sample account summary for testing."""
    # Calculate totals from sample positions
    # AAPL: 10 * 160 = 1600, profit = 100
    # GOOGL: 5 * 1900 = 9500, loss = -500
    # TSLA: 2.5 * 850 = 2125, profit = 125
    # Total invested = 1600 + 9500 + 2125 = 13225
    # Total result = 100 + (-500) + 125 = -275
    
    return AccountSummary(
        free_funds=Decimal("2500.00"),
        invested=Decimal("13225.00"),
        result=Decimal("-275.00"),
        currency="GBP"
    )


@pytest.fixture
def profitable_position():
    """A position with a profit for testing."""
    return Position(
        ticker="PROFIT",
        name="Profitable Stock",
        shares=Decimal("100.0"),
        average_price=Decimal("10.00"),
        current_price=Decimal("15.00"),
        currency="GBP"
    )


@pytest.fixture
def loss_position():
    """A position with a loss for testing."""
    return Position(
        ticker="LOSS",
        name="Loss Stock",
        shares=Decimal("50.0"),
        average_price=Decimal("20.00"),
        current_price=Decimal("15.00"),
        currency="GBP"
    )


@pytest.fixture
def break_even_position():
    """A position that breaks even for testing."""
    return Position(
        ticker="EVEN",
        name="Break Even Stock",
        shares=Decimal("25.0"),
        average_price=Decimal("40.00"),
        current_price=Decimal("40.00"),
        currency="GBP"
    )


@pytest.fixture
def mock_trading212_client():
    """Mock Trading212Client for testing."""
    mock_client = Mock(spec=Trading212Client)
    mock_client.BASE_URL = "https://live.trading212.com/api/v0"
    mock_client._request_interval = 0.5
    return mock_client


@pytest.fixture
def configured_mock_client(mock_trading212_client, mock_api_responses):
    """Mock client with configured responses."""
    mock_trading212_client.get_account_metadata.return_value = mock_api_responses['metadata']
    mock_trading212_client.get_portfolio.return_value = mock_api_responses['portfolio']
    mock_trading212_client.get_account_cash.return_value = mock_api_responses['cash']
    
    def get_position_details_side_effect(ticker):
        return mock_api_responses['position_details'].get(ticker, {'name': ticker})
    
    mock_trading212_client.get_position_details.side_effect = get_position_details_side_effect
    
    return mock_trading212_client


@pytest.fixture
def edge_case_api_responses():
    """Edge case API responses for testing error conditions."""
    return {
        'empty_portfolio': [],
        'zero_balance': {
            'free': 0.0,
            'total': 0.0,
            'currency': 'GBP'
        },
        'missing_currency_metadata': {
            'id': 12345
            # Missing currencyCode
        },
        'position_with_zero_price': {
            'ticker': 'ZERO',
            'quantity': 10.0,
            'averagePrice': 0.0,
            'currentPrice': 0.0,
            'currencyCode': 'GBP'
        },
        'fractional_position': {
            'ticker': 'FRAC',
            'quantity': 0.123456,
            'averagePrice': 123.456789,
            'currentPrice': 234.567890,
            'currencyCode': 'USD'
        }
    }


@pytest.fixture
def large_portfolio_data():
    """Large portfolio data for performance testing."""
    positions = []
    for i in range(100):
        positions.append({
            'ticker': f'STOCK{i:03d}',
            'quantity': float(10 + i),
            'averagePrice': float(100 + i * 2),
            'currentPrice': float(105 + i * 2.1),
            'currencyCode': 'USD' if i % 2 == 0 else 'GBP'
        })
    
    return {
        'portfolio': positions,
        'metadata': {'currencyCode': 'GBP'},
        'cash': {'free': 50000.0, 'total': 150000.0, 'currency': 'GBP'}
    }