"""
Integration tests for portfolio export functionality.
"""

import pytest
from decimal import Decimal

from trading212_exporter import PortfolioExporter


@pytest.mark.integration
@pytest.mark.slow
class TestPortfolioExport:
    """Test complete portfolio export process."""
    
    def test_fetch_data_integration(self, portfolio_exporter):
        """Test fetching real data from the API."""
        portfolio_exporter.fetch_data()
        
        # Verify data was fetched
        assert portfolio_exporter.account_summary is not None
        assert isinstance(portfolio_exporter.account_summary.free_funds, Decimal)
        assert isinstance(portfolio_exporter.positions, list)
    
    def test_generate_markdown_integration(self, portfolio_exporter):
        """Test generating markdown with real data."""
        portfolio_exporter.fetch_data()
        markdown = portfolio_exporter.generate_markdown()
        
        assert isinstance(markdown, str)
        assert "# Trading 212 Portfolio" in markdown
        assert "## Portfolio Positions" in markdown
        assert "## Summary" in markdown
        
        # Check for proper formatting
        assert "FREE FUNDS" in markdown
        assert "PORTFOLIO" in markdown
        assert "RESULT" in markdown
    
    def test_save_to_file_integration(self, portfolio_exporter, tmp_path):
        """Test saving markdown to file."""
        portfolio_exporter.fetch_data()
        
        output_file = tmp_path / "test_portfolio.md"
        portfolio_exporter.save_to_file(str(output_file))
        
        assert output_file.exists()
        
        content = output_file.read_text(encoding='utf-8')
        assert "# Trading 212 Portfolio" in content
        assert len(content) > 0