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
    
    def test_full_export_workflow(self, api_client, tmp_path):
        """Test the complete export workflow end-to-end."""
        exporter = PortfolioExporter(api_client)
        
        # Fetch data
        exporter.fetch_data()
        
        # Verify positions have calculated fields
        for position in exporter.positions:
            assert hasattr(position, 'market_value')
            assert hasattr(position, 'profit_loss')
            assert hasattr(position, 'profit_loss_percent')
            
            # Verify calculations are reasonable
            assert position.market_value >= 0
            assert isinstance(position.profit_loss, Decimal)
            assert isinstance(position.profit_loss_percent, Decimal)
        
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