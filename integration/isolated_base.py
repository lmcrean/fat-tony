"""
Base class for isolated integration tests.

This module provides a foundation for creating truly isolated integration tests
that avoid hallucination issues through strict data validation and independence.
"""

import json
import pytest
from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, create_autospec
from dataclasses import dataclass

from trading212_exporter import Trading212Client, PortfolioExporter
from trading212_exporter.models import Position, AccountSummary


@dataclass
class IsolatedTestData:
    """Container for isolated test data that ensures complete independence."""
    
    account_metadata: Dict[str, Any]
    account_cash: Dict[str, Any]
    portfolio_positions: List[Dict[str, Any]]
    position_details: Dict[str, Dict[str, Any]]
    expected_calculations: Dict[str, Any]
    
    def copy(self) -> 'IsolatedTestData':
        """Create a deep copy of test data to ensure test isolation."""
        return IsolatedTestData(
            account_metadata=json.loads(json.dumps(self.account_metadata)),
            account_cash=json.loads(json.dumps(self.account_cash)),
            portfolio_positions=json.loads(json.dumps(self.portfolio_positions)),
            position_details=json.loads(json.dumps(self.position_details)),
            expected_calculations=json.loads(json.dumps(self.expected_calculations))
        )


class IsolatedIntegrationTestBase(ABC):
    """
    Base class for isolated integration tests.
    
    This class ensures that each test runs in complete isolation with:
    - Independent mock data for each test method
    - Strict data validation against expected schemas
    - No shared state between tests
    - Comprehensive assertion helpers
    """
    
    def setup_method(self):
        """Set up fresh test environment for each test method."""
        self._test_data = self.create_isolated_test_data()
        self._mock_client = self._create_isolated_mock_client()
        self._exporter = PortfolioExporter({self.get_account_name(): self._mock_client})
    
    @abstractmethod
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create isolated test data for this specific test class."""
        pass
    
    @abstractmethod
    def get_account_name(self) -> str:
        """Get the account name for this test class."""
        pass
    
    def _create_isolated_mock_client(self) -> Mock:
        """Create a completely isolated mock client for this test."""
        # Use create_autospec for stricter mocking
        client = create_autospec(Trading212Client, spec_set=True)
        client.account_name = self.get_account_name()
        client._request_interval = 5  # For rate limiting tests
        
        # Configure mock responses with isolated data
        test_data = self._test_data.copy()  # Ensure complete independence
        
        client.get_account_metadata.return_value = test_data.account_metadata
        client.get_account_cash.return_value = test_data.account_cash
        client.get_portfolio.return_value = test_data.portfolio_positions
        
        # Configure position details with strict validation
        def isolated_position_details(ticker: str) -> Dict[str, Any]:
            if ticker in test_data.position_details:
                return test_data.position_details[ticker].copy()
            else:
                # Return minimal valid response for unknown tickers
                return {"ticker": ticker, "name": ticker}
        
        client.get_position_details.side_effect = isolated_position_details
        
        return client
    
    def validate_position_structure(self, position: Position) -> None:
        """Validate that a position has the correct structure and data types."""
        # Validate required attributes exist
        required_attrs = [
            'ticker', 'name', 'shares', 'average_price', 'current_price', 
            'currency', 'account_name', 'market_value', 'profit_loss', 
            'profit_loss_percent', 'cost_basis'
        ]
        
        for attr in required_attrs:
            assert hasattr(position, attr), f"Position missing required attribute: {attr}"
        
        # Validate data types
        assert isinstance(position.ticker, str), f"ticker should be str, got {type(position.ticker)}"
        assert isinstance(position.name, str), f"name should be str, got {type(position.name)}"
        assert isinstance(position.shares, Decimal), f"shares should be Decimal, got {type(position.shares)}"
        assert isinstance(position.average_price, Decimal), f"average_price should be Decimal, got {type(position.average_price)}"
        assert isinstance(position.current_price, Decimal), f"current_price should be Decimal, got {type(position.current_price)}"
        assert isinstance(position.currency, str), f"currency should be str, got {type(position.currency)}"
        assert isinstance(position.account_name, str), f"account_name should be str, got {type(position.account_name)}"
        assert isinstance(position.market_value, Decimal), f"market_value should be Decimal, got {type(position.market_value)}"
        assert isinstance(position.profit_loss, Decimal), f"profit_loss should be Decimal, got {type(position.profit_loss)}"
        assert isinstance(position.profit_loss_percent, Decimal), f"profit_loss_percent should be Decimal, got {type(position.profit_loss_percent)}"
        assert isinstance(position.cost_basis, Decimal), f"cost_basis should be Decimal, got {type(position.cost_basis)}"
        
        # Validate logical constraints
        assert position.shares >= 0, f"shares should be non-negative, got {position.shares}"
        assert position.average_price >= 0, f"average_price should be non-negative, got {position.average_price}"
        assert position.current_price >= 0, f"current_price should be non-negative, got {position.current_price}"
        assert position.market_value >= 0, f"market_value should be non-negative, got {position.market_value}"
        
        # Validate calculations are correct
        expected_cost_basis = position.shares * position.average_price
        expected_market_value = position.shares * position.current_price
        expected_profit_loss = expected_market_value - expected_cost_basis
        
        assert position.cost_basis == expected_cost_basis, \
            f"cost_basis calculation incorrect: expected {expected_cost_basis}, got {position.cost_basis}"
        assert position.market_value == expected_market_value, \
            f"market_value calculation incorrect: expected {expected_market_value}, got {position.market_value}"
        assert position.profit_loss == expected_profit_loss, \
            f"profit_loss calculation incorrect: expected {expected_profit_loss}, got {position.profit_loss}"
        
        # Validate profit/loss percentage calculation
        if expected_cost_basis > 0:
            expected_profit_loss_percent = (expected_profit_loss / expected_cost_basis) * 100
            assert position.profit_loss_percent == expected_profit_loss_percent, \
                f"profit_loss_percent calculation incorrect: expected {expected_profit_loss_percent}, got {position.profit_loss_percent}"
    
    def validate_account_summary_structure(self, summary: AccountSummary) -> None:
        """Validate that an account summary has the correct structure and data types."""
        # Validate required attributes exist
        required_attrs = ['account_name', 'free_funds', 'invested', 'result', 'currency']
        
        for attr in required_attrs:
            assert hasattr(summary, attr), f"AccountSummary missing required attribute: {attr}"
        
        # Validate data types
        assert isinstance(summary.account_name, str), f"account_name should be str, got {type(summary.account_name)}"
        assert isinstance(summary.free_funds, Decimal), f"free_funds should be Decimal, got {type(summary.free_funds)}"
        assert isinstance(summary.invested, Decimal), f"invested should be Decimal, got {type(summary.invested)}"
        assert isinstance(summary.result, Decimal), f"result should be Decimal, got {type(summary.result)}"
        assert isinstance(summary.currency, str), f"currency should be str, got {type(summary.currency)}"
        
        # Validate logical constraints
        assert summary.free_funds >= 0, f"free_funds should be non-negative, got {summary.free_funds}"
        assert summary.invested >= 0, f"invested should be non-negative, got {summary.invested}"
        assert summary.currency in ["USD", "GBP", "EUR"], f"currency should be valid, got {summary.currency}"
        assert summary.account_name == self.get_account_name(), \
            f"account_name should match test account name, got {summary.account_name}"
    
    def validate_markdown_structure(self, markdown: str) -> None:
        """Validate that generated markdown has the correct structure."""
        assert isinstance(markdown, str), f"markdown should be str, got {type(markdown)}"
        assert len(markdown) > 0, "markdown should not be empty"
        
        # Validate required sections
        required_sections = [
            "# Trading 212 Portfolio",
            "Generated on",
            "## Portfolio Positions" if len(self._test_data.portfolio_positions) > 0 else "## Summary",
            "## Summary"
        ]
        
        for section in required_sections:
            assert section in markdown, f"markdown missing required section: {section}"
        
        # Validate table structure if positions exist
        if len(self._test_data.portfolio_positions) > 0:
            table_headers = ["NAME", "SHARES", "AVERAGE PRICE", "CURRENT PRICE", "MARKET VALUE", "RESULT", "RESULT %"]
            for header in table_headers:
                assert header in markdown, f"markdown missing table header: {header}"
            
            # Validate table formatting
            assert "|" in markdown, "markdown should contain table formatting"
            assert "---" in markdown, "markdown should contain table separators"
        
        # Validate summary section
        summary_items = ["FREE FUNDS", "PORTFOLIO", "RESULT"]
        for item in summary_items:
            assert item in markdown, f"markdown missing summary item: {item}"
    
    def assert_exact_calculation_match(self, position: Position, expected: Dict[str, Any]) -> None:
        """Assert that position calculations exactly match expected values."""
        ticker = expected["ticker"]
        
        # Convert expected values to Decimal for exact comparison
        expected_shares = Decimal(str(expected["quantity"]))
        expected_avg_price = Decimal(str(expected["averagePrice"]))
        expected_current_price = Decimal(str(expected["currentPrice"]))
        expected_market_value = expected_shares * expected_current_price
        expected_cost_basis = expected_shares * expected_avg_price
        expected_profit_loss = expected_market_value - expected_cost_basis
        
        # Exact assertions
        assert position.ticker == ticker, f"ticker mismatch for {ticker}"
        assert position.shares == expected_shares, f"shares mismatch for {ticker}: expected {expected_shares}, got {position.shares}"
        assert position.average_price == expected_avg_price, f"average_price mismatch for {ticker}: expected {expected_avg_price}, got {position.average_price}"
        assert position.current_price == expected_current_price, f"current_price mismatch for {ticker}: expected {expected_current_price}, got {position.current_price}"
        assert position.market_value == expected_market_value, f"market_value mismatch for {ticker}: expected {expected_market_value}, got {position.market_value}"
        assert position.cost_basis == expected_cost_basis, f"cost_basis mismatch for {ticker}: expected {expected_cost_basis}, got {position.cost_basis}"
        assert position.profit_loss == expected_profit_loss, f"profit_loss mismatch for {ticker}: expected {expected_profit_loss}, got {position.profit_loss}"
        assert position.currency == expected["currencyCode"], f"currency mismatch for {ticker}"
        assert position.account_name == self.get_account_name(), f"account_name mismatch for {ticker}"
    
    def get_exporter(self) -> PortfolioExporter:
        """Get the isolated exporter for this test."""
        return self._exporter
    
    def get_test_data(self) -> IsolatedTestData:
        """Get the isolated test data for this test."""
        return self._test_data.copy()  # Always return a copy to maintain isolation