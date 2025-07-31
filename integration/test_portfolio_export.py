"""
Integration tests for portfolio export functionality.
"""

import pytest
from decimal import Decimal
from pathlib import Path

from trading212_exporter import PortfolioExporter


@pytest.mark.integration
class TestPortfolioExport:
    """Test complete portfolio export process with mocked data."""
    
    def test_fetch_data_integration_single_account(self, portfolio_exporter):
        """Test fetching data from single account with mocked API."""
        portfolio_exporter.fetch_data()
        
        # Verify data was fetched successfully
        assert portfolio_exporter.account_summaries is not None
        assert len(portfolio_exporter.account_summaries) == 1
        assert "Trading 212" in portfolio_exporter.account_summaries
        
        # Check account summary structure
        account_summary = portfolio_exporter.account_summaries["Trading 212"]
        assert isinstance(account_summary.free_funds, Decimal)
        assert isinstance(account_summary.invested, Decimal)
        assert isinstance(account_summary.result, Decimal)
        assert account_summary.currency == "USD"
        assert account_summary.account_name == "Trading 212"
        
        # Verify positions were fetched
        assert isinstance(portfolio_exporter.positions, list)
        assert len(portfolio_exporter.positions) == 3  # Based on mock data
        
        # Check position structure
        for position in portfolio_exporter.positions:
            assert hasattr(position, 'ticker')
            assert hasattr(position, 'name')
            assert hasattr(position, 'shares')
            assert hasattr(position, 'average_price')
            assert hasattr(position, 'current_price')
            assert hasattr(position, 'currency')
            assert hasattr(position, 'account_name')
            assert position.account_name == "Trading 212"
    
    def test_fetch_data_integration_multi_account(self, multi_account_exporter):
        """Test fetching data from multiple accounts with mocked API."""
        multi_account_exporter.fetch_data()
        
        # Verify data was fetched from both accounts
        assert len(multi_account_exporter.account_summaries) == 2
        assert "Stocks & Shares ISA" in multi_account_exporter.account_summaries
        assert "Invest Account" in multi_account_exporter.account_summaries
        
        # Check ISA account
        isa_summary = multi_account_exporter.account_summaries["Stocks & Shares ISA"]
        assert isa_summary.currency == "GBP"
        assert isa_summary.account_name == "Stocks & Shares ISA"
        
        # Check Invest account
        invest_summary = multi_account_exporter.account_summaries["Invest Account"]
        assert invest_summary.currency == "USD"
        assert invest_summary.account_name == "Invest Account"
        
        # Verify positions from both accounts
        assert len(multi_account_exporter.positions) > 0
        
        # Check that positions have correct account names
        isa_positions = [p for p in multi_account_exporter.positions if p.account_name == "Stocks & Shares ISA"]
        invest_positions = [p for p in multi_account_exporter.positions if p.account_name == "Invest Account"]
        
        assert len(isa_positions) > 0
        assert len(invest_positions) > 0
        
        # Verify GBP positions are in ISA account
        for position in isa_positions:
            assert position.currency == "GBP"
            assert position.ticker in ["VOD.L", "LLOY.L"]
        
        # Verify USD positions are in Invest account  
        for position in invest_positions:
            assert position.currency == "USD"
            assert position.ticker == "AAPL"
    
    def test_fetch_data_with_error_handling(self, error_prone_client):
        """Test data fetching with API errors using mocked error client."""
        exporter = PortfolioExporter({"Trading 212": error_prone_client})
        
        # Should not raise exception, should handle errors gracefully
        exporter.fetch_data()
        
        # Should still have created account summary (with defaults for failed calls)
        assert "Trading 212" in exporter.account_summaries
        account_summary = exporter.account_summaries["Trading 212"]
        
        # Free funds should be zero due to API error
        assert account_summary.free_funds == Decimal('0')
        
        # Should still have positions (since get_portfolio succeeds)
        assert len(exporter.positions) == 1
        
        # Position should use ticker as name due to get_position_details failure
        position = exporter.positions[0]
        assert position.name == position.ticker  # Fallback behavior
    
    def test_generate_markdown_integration_single_account(self, portfolio_exporter):
        """Test generating markdown with single account mocked data."""
        portfolio_exporter.fetch_data()
        markdown = portfolio_exporter.generate_markdown()
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        
        # Check main structure
        assert "# Trading 212 Portfolio" in markdown
        assert "Generated on" in markdown
        assert "## Portfolio Positions" in markdown
        assert "## Summary" in markdown
        
        # Check table headers
        assert "NAME" in markdown
        assert "SHARES" in markdown
        assert "AVERAGE PRICE" in markdown
        assert "CURRENT PRICE" in markdown
        assert "MARKET VALUE" in markdown
        assert "RESULT" in markdown
        assert "RESULT %" in markdown
        
        # Check for position data
        assert "Apple Inc." in markdown
        assert "Alphabet Inc." in markdown
        assert "Tesla Inc." in markdown
        
        # Check for currency formatting
        assert "USD" in markdown  # Should show USD amounts
        
        # Check for profit/loss indicators
        profit_loss_indicators = ["🟢", "🔴", "⚪"]
        assert any(indicator in markdown for indicator in profit_loss_indicators)
        
        # Check summary section formatting
        assert "FREE FUNDS" in markdown
        assert "PORTFOLIO" in markdown
        assert "RESULT" in markdown
    
    def test_generate_markdown_integration_multi_account(self, multi_account_exporter):
        """Test generating markdown with multi-account mocked data."""
        multi_account_exporter.fetch_data()
        markdown = multi_account_exporter.generate_markdown()
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        
        # Check multi-account structure
        assert "# Trading 212 Portfolio" in markdown
        assert "## Stocks & Shares ISA" in markdown
        assert "## Invest Account" in markdown
        
        # Combined Totals only appears if all accounts have same currency
        # Our mock data has GBP and USD, so no combined totals expected
        
        # Check account-specific sections
        assert "### Positions" in markdown
        assert "### Summary" in markdown
        
        # Check for positions from both accounts
        assert "Vodafone Group Plc" in markdown  # ISA position
        assert "Apple Inc." in markdown  # Invest position
        
        # Check currency formatting for both accounts
        assert "GBP" in markdown or "£" in markdown  # ISA account currency
        assert "USD" in markdown  # Invest account currency
        
        # Check combined totals section (only if currencies match)
        currencies = set(summary.currency for summary in multi_account_exporter.account_summaries.values())
        if len(currencies) == 1:
            assert "TOTAL FREE FUNDS" in markdown
            assert "TOTAL PORTFOLIO" in markdown
            assert "TOTAL RESULT" in markdown
        else:
            # Different currencies, so no combined totals
            assert "TOTAL FREE FUNDS" not in markdown
    
    def test_generate_markdown_empty_portfolio(self, empty_portfolio_client):
        """Test generating markdown with empty portfolio."""
        exporter = PortfolioExporter({"Trading 212": empty_portfolio_client})
        exporter.fetch_data()
        markdown = exporter.generate_markdown()
        
        assert isinstance(markdown, str)
        assert "# Trading 212 Portfolio" in markdown
        assert "## Portfolio Positions" in markdown
        assert "## Summary" in markdown
        
        # Should show zero values in summary
        assert "FREE FUNDS" in markdown
        assert "PORTFOLIO" in markdown
        assert "RESULT" in markdown
    
    def test_save_to_file_integration(self, portfolio_exporter, tmp_path):
        """Test saving markdown to file with mocked data."""
        portfolio_exporter.fetch_data()
        
        output_file = tmp_path / "test_portfolio.md"
        portfolio_exporter.save_to_file(str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify file content
        content = output_file.read_text(encoding='utf-8')
        assert "# Trading 212 Portfolio" in content
        assert len(content) > 0
        
        # Check that it contains expected position data
        assert "Apple Inc." in content
        assert "Alphabet Inc." in content
        assert "Tesla Inc." in content
        
        # Check formatting is preserved
        assert "|" in content  # Table formatting
        assert "FREE FUNDS" in content
        assert "PORTFOLIO" in content
    
    def test_save_to_file_default_filename(self, portfolio_exporter, tmp_path, monkeypatch):
        """Test saving to default filename."""
        # Change to temp directory so we don't create files in project root
        monkeypatch.chdir(tmp_path)
        
        portfolio_exporter.fetch_data()
        portfolio_exporter.save_to_file()  # Use default filename
        
        # Check default file was created
        default_file = tmp_path / "portfolio.md"
        assert default_file.exists()
        
        content = default_file.read_text(encoding='utf-8')
        assert "# Trading 212 Portfolio" in content
    
    def test_complete_export_workflow_integration(self, portfolio_exporter, tmp_path):
        """Test the complete export workflow end-to-end with mocked data."""
        # Step 1: Fetch data
        portfolio_exporter.fetch_data()
        
        # Verify data fetching worked
        assert len(portfolio_exporter.positions) > 0
        assert len(portfolio_exporter.account_summaries) > 0
        
        # Step 2: Generate markdown
        markdown = portfolio_exporter.generate_markdown()
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        
        # Step 3: Save to file
        output_file = tmp_path / "integration_test_portfolio.md"
        portfolio_exporter.save_to_file(str(output_file))
        
        # Step 4: Verify final output
        assert output_file.exists()
        
        content = output_file.read_text(encoding='utf-8')
        
        # Check content matches generated markdown
        assert content == markdown
        
        # Verify comprehensive content
        assert "# Trading 212 Portfolio" in content
        assert "Generated on" in content
        assert "Apple Inc." in content
        assert "Tesla Inc." in content
        assert "FREE FUNDS" in content
        assert "PORTFOLIO" in content
        assert "RESULT" in content
        
        # Check for profit/loss indicators
        profit_loss_indicators = ["🟢", "🔴", "⚪"]
        assert any(indicator in content for indicator in profit_loss_indicators)
    
    def test_export_with_fractional_shares(self, mock_fixture_data, tmp_path):
        """Test export with fractional shares."""
        from unittest.mock import Mock
        from trading212_exporter import Trading212Client
        
        # Create client with fractional shares
        fractional_client = Mock(spec=Trading212Client)
        fractional_client.account_name = 'Trading 212'
        fractional_client.get_account_metadata.return_value = mock_fixture_data['account_metadata']['success']
        fractional_client.get_account_cash.return_value = mock_fixture_data['account_cash']['gbp_account']
        fractional_client.get_portfolio.return_value = mock_fixture_data['portfolio_positions']['fractional_shares']
        
        def fractional_position_details(ticker):
            return mock_fixture_data['position_details'].get(ticker, {'ticker': ticker, 'name': f'{ticker} Inc.'})
        fractional_client.get_position_details.side_effect = fractional_position_details
        
        exporter = PortfolioExporter({"Trading 212": fractional_client})
        exporter.fetch_data()
        
        # Verify fractional shares are handled correctly
        assert len(exporter.positions) == 1
        position = exporter.positions[0]
        assert position.ticker == "AMZN"
        assert position.shares == Decimal('0.5')
        
        # Generate markdown and verify fractional formatting
        markdown = exporter.generate_markdown()
        assert "0.5" in markdown  # Should show fractional shares
        
        # Save and verify
        output_file = tmp_path / "fractional_test.md"
        exporter.save_to_file(str(output_file))
        
        content = output_file.read_text(encoding='utf-8')
        assert "0.5" in content