"""
Unit tests for PortfolioExporter class.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from decimal import Decimal
import tempfile
import os

from trading212_exporter import PortfolioExporter, Trading212Client, Position, AccountSummary


class TestPortfolioExporter:
    """Unit tests for PortfolioExporter."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Trading212Client."""
        client = Mock(spec=Trading212Client)
        return client
    
    @pytest.fixture
    def exporter(self, mock_client):
        """Create a PortfolioExporter with mock client."""
        return PortfolioExporter(mock_client)
    
    @pytest.fixture
    def sample_positions(self):
        """Create sample positions for testing."""
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
                name="Alphabet Inc.",
                shares=Decimal("5.0"),
                average_price=Decimal("2000.00"),
                current_price=Decimal("1900.00"),
                currency="USD"
            )
        ]
    
    @pytest.fixture
    def sample_account_summary(self):
        """Create sample account summary for testing."""
        return AccountSummary(
            free_funds=Decimal("1000.00"),
            invested=Decimal("11100.00"),  # 1600 + 9500
            result=Decimal("-400.00"),     # 100 + (-500)
            currency="USD"
        )
    
    def test_exporter_initialization(self, mock_client):
        """Test exporter initialization."""
        exporter = PortfolioExporter(mock_client)
        assert exporter.client == mock_client
        assert exporter.positions == []
        assert exporter.account_summary is None
    
    def test_fetch_data_success(self, exporter, mock_client):
        """Test successful data fetching."""
        # Mock API responses
        mock_client.get_account_metadata.return_value = {"currencyCode": "USD"}
        mock_client.get_portfolio.return_value = [
            {
                "ticker": "AAPL",
                "quantity": 10.0,
                "averagePrice": 150.0,
                "currentPrice": 160.0,
                "currencyCode": "USD"
            }
        ]
        mock_client.get_position_details.return_value = {
            "name": "Apple Inc.",
            "ticker": "AAPL"
        }
        mock_client.get_account_cash.return_value = {"free": 1000.0}
        
        exporter.fetch_data()
        
        # Verify positions were created
        assert len(exporter.positions) == 1
        position = exporter.positions[0]
        assert position.ticker == "AAPL"
        assert position.name == "Apple Inc."
        assert position.shares == Decimal("10.0")
        
        # Verify account summary was created
        assert exporter.account_summary is not None
        assert exporter.account_summary.free_funds == Decimal("1000.0")
    
    def test_fetch_data_with_api_error(self, exporter, mock_client):
        """Test data fetching with API error for position details."""
        mock_client.get_account_metadata.return_value = {"currencyCode": "USD"}
        mock_client.get_portfolio.return_value = [
            {
                "ticker": "AAPL",
                "quantity": 10.0,
                "averagePrice": 150.0,
                "currentPrice": 160.0,
                "currencyCode": "USD"
            }
        ]
        mock_client.get_position_details.side_effect = Exception("API Error")
        mock_client.get_account_cash.return_value = {"free": 1000.0}
        
        exporter.fetch_data()
        
        # Should still create position with basic data
        assert len(exporter.positions) == 1
        position = exporter.positions[0]
        assert position.ticker == "AAPL"
        assert position.name == "AAPL"  # Falls back to ticker
    
    def test_format_currency(self, exporter):
        """Test currency formatting."""
        assert exporter._format_currency(Decimal("100.50"), "GBP") == "£100.50"
        assert exporter._format_currency(Decimal("1000.00"), "USD") == "USD1,000.00"
        assert exporter._format_currency(Decimal("0.01"), "GBP") == "£0.01"
    
    def test_format_percentage(self, exporter):
        """Test percentage formatting with indicators."""
        assert exporter._format_percentage(Decimal("10.50")) == "🟢 +10.50%"
        assert exporter._format_percentage(Decimal("-5.25")) == "🔴 -5.25%"
        assert exporter._format_percentage(Decimal("0.00")) == "⚪ +0.00%"
    
    def test_format_profit_loss(self, exporter):
        """Test profit/loss formatting with indicators."""
        assert exporter._format_profit_loss(Decimal("100.00")) == "🟢 £100.00"
        assert exporter._format_profit_loss(Decimal("-50.00")) == "🔴 £-50.00"
        assert exporter._format_profit_loss(Decimal("0.00")) == "⚪ £0.00"
    
    def test_generate_markdown_empty_portfolio(self, exporter):
        """Test markdown generation with empty portfolio."""
        exporter.account_summary = AccountSummary(
            free_funds=Decimal("1000.00"),
            invested=Decimal("0.00"),
            result=Decimal("0.00")
        )
        
        markdown = exporter.generate_markdown()
        
        assert "# Trading 212 Portfolio" in markdown
        assert "## Portfolio Positions" in markdown
        assert "## Summary" in markdown
        assert "FREE FUNDS" in markdown
        assert "£1,000.00" in markdown
    
    def test_generate_markdown_with_positions(self, exporter, sample_positions, sample_account_summary):
        """Test markdown generation with positions."""
        exporter.positions = sample_positions
        exporter.account_summary = sample_account_summary
        
        markdown = exporter.generate_markdown()
        
        # Check header
        assert "# Trading 212 Portfolio" in markdown
        assert "Generated on" in markdown
        
        # Check table content
        assert "Apple Inc." in markdown
        assert "Alphabet Inc." in markdown
        assert "🟢" in markdown  # For profit
        assert "🔴" in markdown  # For loss
        
        # Check summary
        assert "FREE FUNDS" in markdown
        assert "PORTFOLIO" in markdown
        assert "RESULT" in markdown
        assert "USD1,000.00" in markdown
    
    def test_save_to_file(self, exporter, sample_positions, sample_account_summary):
        """Test saving markdown to file."""
        exporter.positions = sample_positions
        exporter.account_summary = sample_account_summary
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            exporter.save_to_file(temp_filename)
            
            # Verify file was created and contains expected content
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "# Trading 212 Portfolio" in content
            assert "Apple Inc." in content
            assert "Alphabet Inc." in content
            
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_save_to_file_default_name(self, mock_print, mock_file, exporter):
        """Test saving to default filename."""
        exporter.positions = []
        exporter.account_summary = AccountSummary(
            free_funds=Decimal("100.00"),
            invested=Decimal("0.00"),
            result=Decimal("0.00")
        )
        
        exporter.save_to_file()
        
        # Verify default filename was used
        mock_file.assert_called_once_with("portfolio.md", 'w', encoding='utf-8')
        mock_print.assert_called_once_with("\nPortfolio exported successfully to portfolio.md")