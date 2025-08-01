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
            currency="USD",
            account_name="Trading 212"
        )
    
    def test_exporter_initialization(self, mock_client):
        """Test exporter initialization."""
        exporter = PortfolioExporter(mock_client)
        assert "Trading 212" in exporter.clients
        assert exporter.clients["Trading 212"] == mock_client
        assert exporter.positions == []
        assert exporter.account_summaries == {}
    
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
        assert len(exporter.account_summaries) == 1
        assert "Trading 212" in exporter.account_summaries
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.free_funds == Decimal("1000.0")
    
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
        exporter.account_summaries["Trading 212"] = AccountSummary(
            free_funds=Decimal("1000.00"),
            invested=Decimal("0.00"),
            result=Decimal("0.00"),
            currency="GBP",
            account_name="Trading 212"
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
        exporter.account_summaries["Trading 212"] = sample_account_summary
        
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
        exporter.account_summaries["Trading 212"] = sample_account_summary
        
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
        exporter.account_summaries["Trading 212"] = AccountSummary(
            free_funds=Decimal("100.00"),
            invested=Decimal("0.00"),
            result=Decimal("0.00"),
            currency="GBP",
            account_name="Trading 212"
        )
        
        exporter.save_to_file()
        
        # Verify default filename was used
        mock_file.assert_called_once_with("portfolio.md", 'w', encoding='utf-8')
        mock_print.assert_called_once_with("\nPortfolio exported successfully to portfolio.md")
    
    def test_generate_markdown_multi_account(self, mock_client):
        """Test markdown generation with multiple accounts."""
        # Create exporter with multiple clients
        mock_client2 = Mock(spec=Trading212Client)
        exporter = PortfolioExporter({
            "Trading 212": mock_client,
            "Trading 212 ISA": mock_client2
        })
        
        # Add positions for different accounts
        exporter.positions = [
            Position(
                ticker="AAPL",
                name="Apple Inc.",
                shares=Decimal("10"),
                average_price=Decimal("150.00"),
                current_price=Decimal("160.00"),
                currency="USD",
                account_name="Trading 212"
            ),
            Position(
                ticker="GOOGL",
                name="Alphabet Inc.",
                shares=Decimal("5"),
                average_price=Decimal("2000.00"),
                current_price=Decimal("1900.00"),
                currency="USD",
                account_name="Trading 212 ISA"
            )
        ]
        
        # Add account summaries for both accounts
        exporter.account_summaries["Trading 212"] = AccountSummary(
            free_funds=Decimal("500.00"),
            invested=Decimal("1600.00"),
            result=Decimal("100.00"),
            currency="USD",
            account_name="Trading 212"
        )
        exporter.account_summaries["Trading 212 ISA"] = AccountSummary(
            free_funds=Decimal("300.00"),
            invested=Decimal("9500.00"),
            result=Decimal("-500.00"),
            currency="USD",
            account_name="Trading 212 ISA"
        )
        
        markdown = exporter.generate_markdown()
        
        # Check multi-account structure
        assert "## Trading 212" in markdown
        assert "## Trading 212 ISA" in markdown
        assert "## Combined Totals" in markdown
        assert "### Positions" in markdown
        assert "### Summary" in markdown
        
        # Check individual account data
        assert "Apple Inc." in markdown
        assert "Alphabet Inc." in markdown
        
        # Check combined totals
        assert "TOTAL FREE FUNDS" in markdown
        assert "TOTAL PORTFOLIO" in markdown
        assert "TOTAL RESULT" in markdown
        
    def test_exporter_initialization_with_dict(self, mock_client):
        """Test exporter initialization with dictionary of clients."""
        mock_client2 = Mock(spec=Trading212Client)
        clients = {
            "Trading 212": mock_client,
            "Trading 212 ISA": mock_client2
        }
        exporter = PortfolioExporter(clients)
        
        assert len(exporter.clients) == 2
        assert exporter.clients["Trading 212"] == mock_client
        assert exporter.clients["Trading 212 ISA"] == mock_client2
        
    def test_fetch_data_with_metadata_error(self, exporter, mock_client):
        """Test fetch_data when get_account_metadata fails."""
        # Mock metadata to raise exception
        mock_client.get_account_metadata.side_effect = Exception("API permission denied")
        mock_client.get_portfolio.return_value = []
        mock_client.get_account_cash.return_value = {"free": 100.0}
        
        # Should not raise exception, should use default currency
        exporter.fetch_data()
        
        # Verify it continued with default currency
        assert "Trading 212" in exporter.account_summaries
        
    def test_fetch_data_with_cash_error(self, exporter, mock_client):
        """Test fetch_data when get_account_cash fails."""
        mock_client.get_account_metadata.return_value = {"currencyCode": "USD"}
        mock_client.get_portfolio.return_value = []
        mock_client.get_account_cash.side_effect = Exception("API permission denied")
        
        # Should not raise exception, should use default free funds (0)
        exporter.fetch_data()
        
        # Verify it continued with zero free funds
        assert "Trading 212" in exporter.account_summaries
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.free_funds == Decimal("0")
    
    def test_format_currency_csv(self, exporter):
        """Test CSV currency formatting (no symbols)."""
        assert exporter._format_currency_csv(Decimal("100.50"), "GBP") == "100.50"
        assert exporter._format_currency_csv(Decimal("1000.00"), "USD") == "1,000.00"
        assert exporter._format_currency_csv(Decimal("0.01"), "GBP") == "0.01"
    
    def test_format_percentage_csv(self, exporter):
        """Test CSV percentage formatting (no color indicators)."""
        assert exporter._format_percentage_csv(Decimal("10.50")) == "+10.50%"
        assert exporter._format_percentage_csv(Decimal("-5.25")) == "-5.25%"
        assert exporter._format_percentage_csv(Decimal("0.00")) == "+0.00%"
    
    def test_format_profit_loss_csv(self, exporter):
        """Test CSV profit/loss formatting (no color indicators)."""
        assert exporter._format_profit_loss_csv(Decimal("100.00")) == "+100.00"
        assert exporter._format_profit_loss_csv(Decimal("-50.00")) == "-50.00"
        assert exporter._format_profit_loss_csv(Decimal("0.00")) == "+0.00"
    
    def test_generate_positions_csv(self, exporter, sample_positions, sample_account_summary):
        """Test CSV positions generation."""
        exporter.positions = sample_positions
        exporter.account_summaries["Trading 212"] = sample_account_summary
        
        csv_data = exporter.generate_positions_csv()
        
        # Check header
        assert "Trading 212 Portfolio Positions" in csv_data[0][0]
        assert "Generated on" in csv_data[0][0]
        
        # Check column headers
        headers = csv_data[2]
        expected_headers = ["NAME", "SHARES", "AVERAGE_PRICE", "CURRENT_PRICE", "MARKET_VALUE", "RESULT", "RESULT_%", "CURRENCY"]
        assert headers == expected_headers
        
        # Check position data (sorted by market value, Alphabet should be first)
        alphabet_row = csv_data[3]
        assert alphabet_row[0] == "Alphabet Inc."
        assert alphabet_row[1] == "5"
        assert alphabet_row[2] == "2,000.00"
        assert alphabet_row[3] == "1,900.00"
        assert alphabet_row[4] == "9,500.00"
        assert alphabet_row[5] == "-500.00"
        assert alphabet_row[6] == "-5.00%"
        assert alphabet_row[7] == "USD"
        
        # Check Apple row (second largest)
        apple_row = csv_data[4]
        assert apple_row[0] == "Apple Inc."
        assert apple_row[1] == "10"
        assert apple_row[2] == "150.00"
        assert apple_row[3] == "160.00"
        assert apple_row[4] == "1,600.00"
        assert apple_row[5] == "+100.00"
        assert apple_row[6] == "+6.67%"
        assert apple_row[7] == "USD"
    
    def test_generate_summary_csv(self, exporter, sample_positions, sample_account_summary):
        """Test CSV summary generation."""
        exporter.positions = sample_positions
        exporter.account_summaries["Trading 212"] = sample_account_summary
        
        csv_data = exporter.generate_summary_csv()
        
        # Check header
        assert "Trading 212 Portfolio Summary" in csv_data[0][0]
        
        # Check summary structure
        assert csv_data[2] == ["SUMMARY"]
        assert csv_data[3] == ["FREE_FUNDS", "PORTFOLIO", "RESULT", "CURRENCY"]
        
        # Check summary data
        summary_row = csv_data[4]
        assert summary_row[0] == "1,000.00"
        assert summary_row[1] == "11,100.00"
        assert summary_row[2] == "-400.00"
        assert summary_row[3] == "USD"
    
    def test_save_to_csv(self, exporter, sample_positions, sample_account_summary):
        """Test saving CSV to files."""
        exporter.positions = sample_positions
        exporter.account_summaries["Trading 212"] = sample_account_summary
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_positions.csv', delete=False) as pos_file, \
             tempfile.NamedTemporaryFile(mode='w', suffix='_summary.csv', delete=False) as sum_file:
            pos_filename = pos_file.name
            sum_filename = sum_file.name
        
        try:
            exporter.save_to_csv(pos_filename, sum_filename)
            
            # Verify both files were created
            assert os.path.exists(pos_filename)
            assert os.path.exists(sum_filename)
            
            # Verify positions file content
            with open(pos_filename, 'r', encoding='utf-8') as f:
                pos_content = f.read()
            assert "Apple Inc." in pos_content
            assert "Alphabet Inc." in pos_content
            assert "160.00" in pos_content
            
            # Verify summary file content  
            with open(sum_filename, 'r', encoding='utf-8') as f:
                sum_content = f.read()
            assert "SUMMARY" in sum_content
            assert "1,000.00" in sum_content
            
        finally:
            # Clean up
            for filename in [pos_filename, sum_filename]:
                if os.path.exists(filename):
                    os.unlink(filename)