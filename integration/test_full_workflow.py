"""
Integration tests for the complete export workflow.
"""

import pytest
from decimal import Decimal

from trading212_exporter import PortfolioExporter


@pytest.mark.integration
@pytest.mark.slow
class TestFullWorkflow:
    """Test the complete export workflow end-to-end."""
    
    def test_full_export_workflow(self, portfolio_exporter, tmp_path):
        """Test the complete export workflow end-to-end."""
        exporter = portfolio_exporter
        
        # Fetch data
        exporter.fetch_data()
        
        # Verify positions have calculated fields
        for position in exporter.positions:
            assert hasattr(position, 'market_value')
            assert hasattr(position, 'profit_loss')
            assert hasattr(position, 'profit_loss_percent')
            assert hasattr(position, 'account_name')
            
            # Verify calculations are reasonable
            assert position.market_value >= 0
            assert isinstance(position.profit_loss, Decimal)
            assert isinstance(position.profit_loss_percent, Decimal)
            assert position.account_name is not None
        
        # Generate and save output
        output_file = tmp_path / "integration_test_portfolio.md"
        exporter.save_to_file(str(output_file))
        
        # Verify file contents
        content = output_file.read_text(encoding='utf-8')
        
        # Check for emoji indicators
        has_indicators = any(emoji in content for emoji in ['🟢', '🔴', '⚪'])
        assert has_indicators, "Markdown should contain profit/loss indicators"
        
        # Check for currency formatting
        assert '£' in content or 'GBP' in content, "Should contain currency formatting"
    
    def test_multi_account_export_workflow(self, multi_account_exporter, tmp_path):
        """Test the complete multi-account export workflow."""
        exporter = multi_account_exporter
        
        # Fetch data from all accounts
        exporter.fetch_data()
        
        # Verify positions have account names
        for position in exporter.positions:
            assert hasattr(position, 'account_name')
            assert position.account_name in exporter.clients.keys()
        
        # Verify account summaries exist
        assert len(exporter.account_summaries) > 0
        for account_name, summary in exporter.account_summaries.items():
            assert account_name in exporter.clients.keys()
            assert hasattr(summary, 'account_name')
            assert summary.account_name == account_name
        
        # Generate and save output
        output_file = tmp_path / "multi_account_portfolio.md"
        exporter.save_to_file(str(output_file))
        
        # Verify file contents
        content = output_file.read_text(encoding='utf-8')
        
        # If multiple accounts, should have account headers
        if len(exporter.clients) > 1:
            for account_name in exporter.clients.keys():
                assert f"## {account_name}" in content, f"Should contain header for {account_name}"
            
            # Should have combined totals if currencies match
            currencies = set(summary.currency for summary in exporter.account_summaries.values())
            if len(currencies) == 1:
                assert "## Combined Totals" in content, "Should contain combined totals section"