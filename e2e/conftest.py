"""
Pytest configuration and fixtures for end-to-end tests.
"""

import json
import pytest
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock

from trading212_exporter import Trading212Client, PortfolioExporter
from trading212_exporter.models import Position, AccountSummary


@pytest.fixture
def e2e_fixtures_dir():
    """Path to e2e test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def source_of_truth_data(e2e_fixtures_dir):
    """Load source of truth reference data for validation."""
    with open(e2e_fixtures_dir / "source_of_truth_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def spot_check_client(source_of_truth_data):
    """Mock client that returns source of truth data for spot check tickers."""
    client = Mock(spec=Trading212Client)
    
    # Create positions for our target tickers
    positions_data = []
    for ticker_data in source_of_truth_data["target_tickers"]:
        positions_data.append({
            "ticker": ticker_data["ticker"],
            "quantity": ticker_data["shares"],
            "averagePrice": ticker_data["average_price_numeric"],
            "currentPrice": ticker_data["current_price_numeric"],
            "ppl": ticker_data["profit_loss_numeric"],
            "fxPpl": 0.0,
            "pieQuantity": 0.0
        })
    
    client.get_portfolio.return_value = positions_data
    
    # Mock account cash
    client.get_account_cash.return_value = {
        "free": 850.75,
        "invested": sum(pos["quantity"] * pos["currentPrice"] for pos in positions_data),
        "result": sum(pos["ppl"] for pos in positions_data),
        "currency": "GBP"
    }
    
    # Mock account metadata
    client.get_account_metadata.return_value = {
        "accountType": "INVEST",
        "currency": "GBP"
    }
    
    # Mock position details for ticker name resolution
    def mock_position_details(ticker):
        for ticker_data in source_of_truth_data["target_tickers"]:
            if ticker_data["ticker"] == ticker:
                return {"name": ticker_data["name"]}
        return {"name": ticker}
    
    client.get_position_details.side_effect = mock_position_details
    
    return client


@pytest.fixture
def e2e_exporter(spot_check_client):
    """Portfolio exporter configured with spot check client."""
    return PortfolioExporter({"Trading 212": spot_check_client})


@pytest.fixture
def tolerance_config():
    """Configuration for acceptable tolerances in spot check validation."""
    return {
        "price_tolerance": Decimal("0.01"),  # ±1 penny
        "percentage_tolerance": Decimal("0.001"),  # ±0.001%
        "calculation_tolerance": Decimal("0.01")  # ±1 penny for calculated values
    }


@pytest.fixture
def validation_helpers():
    """Helper functions for validation in e2e tests."""
    
    def assert_within_tolerance(actual, expected, tolerance, field_name=""):
        """Assert that actual value is within tolerance of expected value."""
        if isinstance(actual, (int, float)):
            actual = Decimal(str(actual))
        if isinstance(expected, (int, float)):
            expected = Decimal(str(expected))
            
        diff = abs(actual - expected)
        assert diff <= tolerance, (
            f"{field_name} difference too large: "
            f"actual={actual}, expected={expected}, diff={diff}, tolerance={tolerance}"
        )
    
    def validate_position_calculations(position, reference):
        """Validate that position calculations match reference data."""
        # Market value = shares × current price
        expected_market_value = position.shares * position.current_price
        assert position.market_value == expected_market_value, (
            f"Market value calculation incorrect: {position.market_value} != {expected_market_value}"
        )
        
        # Cost basis = shares × average price
        expected_cost_basis = position.shares * position.average_price
        assert position.cost_basis == expected_cost_basis, (
            f"Cost basis calculation incorrect: {position.cost_basis} != {expected_cost_basis}"
        )
        
        # Profit/loss = market value - cost basis
        expected_profit_loss = expected_market_value - expected_cost_basis
        assert position.profit_loss == expected_profit_loss, (
            f"Profit/loss calculation incorrect: {position.profit_loss} != {expected_profit_loss}"
        )
        
        # Profit/loss percentage
        if expected_cost_basis != 0:
            expected_percentage = (expected_profit_loss / expected_cost_basis) * 100
            assert position.profit_loss_percent == expected_percentage, (
                f"Profit/loss percentage incorrect: {position.profit_loss_percent} != {expected_percentage}"
            )
    
    return {
        "assert_within_tolerance": assert_within_tolerance,
        "validate_position_calculations": validate_position_calculations
    }