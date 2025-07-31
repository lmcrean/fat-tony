"""
Unit tests for data models (Position, AccountSummary).
"""

import pytest
from decimal import Decimal

from trading212_exporter import Position, AccountSummary


class TestPosition:
    """Unit tests for Position data model."""
    
    @pytest.fixture
    def sample_position(self):
        """Create a sample position for testing."""
        return Position(
            ticker="AAPL",
            name="Apple Inc.",
            shares=Decimal("10.0"),
            average_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
            currency="USD"
        )
    
    def test_position_creation(self, sample_position):
        """Test position object creation."""
        assert sample_position.ticker == "AAPL"
        assert sample_position.name == "Apple Inc."
        assert sample_position.shares == Decimal("10.0")
        assert sample_position.average_price == Decimal("150.00")
        assert sample_position.current_price == Decimal("160.00")
        assert sample_position.currency == "USD"
    
    def test_market_value_calculation(self, sample_position):
        """Test market value calculation."""
        expected_market_value = Decimal("10.0") * Decimal("160.00")
        assert sample_position.market_value == expected_market_value
        assert sample_position.market_value == Decimal("1600.00")
    
    def test_cost_basis_calculation(self, sample_position):
        """Test cost basis calculation."""
        expected_cost_basis = Decimal("10.0") * Decimal("150.00")
        assert sample_position.cost_basis == expected_cost_basis
        assert sample_position.cost_basis == Decimal("1500.00")
    
    def test_profit_loss_calculation(self, sample_position):
        """Test profit/loss calculation."""
        expected_profit = Decimal("1600.00") - Decimal("1500.00")
        assert sample_position.profit_loss == expected_profit
        assert sample_position.profit_loss == Decimal("100.00")
    
    def test_profit_loss_percent_calculation(self, sample_position):
        """Test profit/loss percentage calculation."""
        # (1600 - 1500) / 1500 * 100 = 6.67%
        expected_percent = Decimal("100.00") / Decimal("1500.00") * 100
        assert sample_position.profit_loss_percent == expected_percent
        assert abs(sample_position.profit_loss_percent - Decimal("6.67")) < Decimal("0.01")
    
    def test_loss_calculation(self):
        """Test calculation with a loss."""
        position = Position(
            ticker="LOSS",
            name="Loss Stock",
            shares=Decimal("5.0"),
            average_price=Decimal("100.00"),
            current_price=Decimal("80.00"),
            currency="USD"
        )
        
        assert position.market_value == Decimal("400.00")
        assert position.cost_basis == Decimal("500.00")
        assert position.profit_loss == Decimal("-100.00")
        assert position.profit_loss_percent == Decimal("-20.00")
    
    def test_zero_cost_basis_edge_case(self):
        """Test edge case where cost basis is zero."""
        position = Position(
            ticker="FREE",
            name="Free Stock",
            shares=Decimal("10.0"),
            average_price=Decimal("0.00"),
            current_price=Decimal("50.00"),
            currency="USD"
        )
        
        assert position.cost_basis == Decimal("0.00")
        assert position.market_value == Decimal("500.00")
        assert position.profit_loss == Decimal("500.00")
        assert position.profit_loss_percent == Decimal("0")  # Should handle division by zero
    
    def test_fractional_shares(self):
        """Test position with fractional shares."""
        position = Position(
            ticker="FRAC",
            name="Fractional Stock",
            shares=Decimal("0.5"),
            average_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            currency="USD"
        )
        
        assert position.market_value == Decimal("55.00")
        assert position.cost_basis == Decimal("50.00")
        assert position.profit_loss == Decimal("5.00")
        assert position.profit_loss_percent == Decimal("10.00")


class TestAccountSummary:
    """Unit tests for AccountSummary data model."""
    
    def test_account_summary_creation(self):
        """Test account summary object creation."""
        summary = AccountSummary(
            free_funds=Decimal("1000.00"),
            invested=Decimal("5000.00"),
            result=Decimal("500.00"),
            currency="GBP"
        )
        
        assert summary.free_funds == Decimal("1000.00")
        assert summary.invested == Decimal("5000.00")
        assert summary.result == Decimal("500.00")
        assert summary.currency == "GBP"
    
    def test_account_summary_default_currency(self):
        """Test account summary with default currency."""
        summary = AccountSummary(
            free_funds=Decimal("500.00"),
            invested=Decimal("2000.00"),
            result=Decimal("-100.00")
        )
        
        assert summary.currency == "GBP"  # Default currency
        assert summary.result == Decimal("-100.00")  # Loss
    
    def test_account_summary_with_loss(self):
        """Test account summary with negative result."""
        summary = AccountSummary(
            free_funds=Decimal("200.00"),
            invested=Decimal("1000.00"),
            result=Decimal("-200.00"),
            currency="USD"
        )
        
        assert summary.result < 0
        assert summary.currency == "USD"