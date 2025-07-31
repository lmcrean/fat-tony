"""
Integration tests for the complete export workflow.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from trading212_exporter import PortfolioExporter, Trading212Client


@pytest.mark.integration
class TestFullWorkflow:
    """Test the complete export workflow end-to-end with mocked data."""
    
    def test_full_export_workflow_single_account(self, portfolio_exporter, tmp_path):
        """Test the complete export workflow end-to-end for single account."""
        exporter = portfolio_exporter
        
        # Step 1: Fetch data
        print("\n--- Step 1: Fetching data ---")
        exporter.fetch_data()
        
        # Verify data was fetched successfully
        assert len(exporter.positions) > 0, "Should have fetched positions"
        assert len(exporter.account_summaries) == 1, "Should have one account summary"
        assert "Trading 212" in exporter.account_summaries
        
        # Step 2: Verify positions have all calculated fields
        print("--- Step 2: Verifying position data ---")
        for position in exporter.positions:
            assert hasattr(position, 'market_value')
            assert hasattr(position, 'profit_loss')
            assert hasattr(position, 'profit_loss_percent')
            assert hasattr(position, 'account_name')
            assert hasattr(position, 'cost_basis')
            
            # Verify calculations are reasonable
            assert position.market_value >= 0
            assert isinstance(position.profit_loss, Decimal)
            assert isinstance(position.profit_loss_percent, Decimal)
            assert position.account_name == "Trading 212"
            
            # Verify calculation consistency
            expected_cost = position.shares * position.average_price
            expected_market = position.shares * position.current_price
            expected_profit = expected_market - expected_cost
            
            assert position.cost_basis == expected_cost
            assert position.market_value == expected_market
            assert position.profit_loss == expected_profit
        
        # Step 3: Verify account summary calculations
        print("--- Step 3: Verifying account summary ---")
        account_summary = exporter.account_summaries["Trading 212"]
        
        # Verify summary matches position totals
        total_market_value = sum(p.market_value for p in exporter.positions)
        total_profit_loss = sum(p.profit_loss for p in exporter.positions)
        
        assert account_summary.invested == total_market_value
        assert account_summary.result == total_profit_loss
        assert account_summary.free_funds == Decimal('850.75')  # From mock data
        assert account_summary.currency == "USD"
        
        # Step 4: Generate markdown
        print("--- Step 4: Generating markdown ---")
        markdown = exporter.generate_markdown()
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "# Trading 212 Portfolio" in markdown
        assert "Generated on" in markdown
        
        # Step 5: Save to file
        print("--- Step 5: Saving to file ---")
        output_file = tmp_path / "full_workflow_test.md"
        exporter.save_to_file(str(output_file))
        
        # Step 6: Verify final output
        print("--- Step 6: Verifying final output ---")
        assert output_file.exists()
        
        content = output_file.read_text(encoding='utf-8')
        
        # Verify content matches generated markdown
        assert content == markdown
        
        # Check for comprehensive content
        assert "Apple Inc." in content
        assert "Alphabet Inc." in content 
        assert "Tesla Inc." in content
        
        # Check for emoji indicators
        profit_loss_indicators = ['🟢', '🔴', '⚪']
        has_indicators = any(emoji in content for emoji in profit_loss_indicators)
        assert has_indicators, "Markdown should contain profit/loss indicators"
        
        # Check for currency formatting
        assert 'USD' in content, "Should contain USD currency formatting"
        
        # Check table structure
        assert "|" in content, "Should contain table formatting"
        assert "NAME" in content
        assert "SHARES" in content
        assert "MARKET VALUE" in content
        assert "RESULT" in content
        
        # Check summary section
        assert "FREE FUNDS" in content
        assert "PORTFOLIO" in content
        assert "RESULT" in content
        
        print("✓ Full workflow test completed successfully")
    
    def test_multi_account_export_workflow(self, multi_account_exporter, tmp_path):
        """Test the complete multi-account export workflow."""
        exporter = multi_account_exporter
        
        # Step 1: Fetch data from all accounts
        print("\n--- Multi-Account Workflow: Step 1 ---")
        exporter.fetch_data()
        
        # Verify data from both accounts
        assert len(exporter.account_summaries) == 2
        assert "Stocks & Shares ISA" in exporter.account_summaries
        assert "Invest Account" in exporter.account_summaries
        
        # Step 2: Verify positions have correct account attribution
        print("--- Step 2: Verifying multi-account position data ---")
        for position in exporter.positions:
            assert hasattr(position, 'account_name')
            assert position.account_name in exporter.clients.keys()
            
            # Verify account-specific data
            if position.account_name == "Stocks & Shares ISA":
                assert position.currency == "GBP"
                assert position.ticker in ["VOD.L", "LLOY.L"]
            elif position.account_name == "Invest Account":
                assert position.currency == "USD"
                assert position.ticker == "AAPL"
        
        # Step 3: Verify account summaries
        print("--- Step 3: Verifying account summaries ---")
        for account_name, summary in exporter.account_summaries.items():
            assert account_name in exporter.clients.keys()
            assert hasattr(summary, 'account_name')
            assert summary.account_name == account_name
            
            # Verify currency consistency
            if account_name == "Stocks & Shares ISA":
                assert summary.currency == "GBP"
                assert summary.free_funds == Decimal('500.25')
            elif account_name == "Invest Account":
                assert summary.currency == "USD"
                assert summary.free_funds == Decimal('850.75')
        
        # Step 4: Generate and save multi-account output
        print("--- Step 4: Generating multi-account markdown ---")
        output_file = tmp_path / "multi_account_workflow.md"
        exporter.save_to_file(str(output_file))
        
        # Step 5: Verify multi-account file contents
        print("--- Step 5: Verifying multi-account output ---")
        content = output_file.read_text(encoding='utf-8')
        
        # Check multi-account structure
        assert "# Trading 212 Portfolio" in content
        assert "## Stocks & Shares ISA" in content
        assert "## Invest Account" in content
        
        # Check account-specific sections
        assert "### Positions" in content
        assert "### Summary" in content
        
        # Check for positions from both accounts
        assert "Vodafone Group Plc" in content  # ISA position
        assert "Apple Inc." in content  # Invest position
        
        # Check currency handling
        assert "GBP" in content or "£" in content  # ISA currency
        assert "USD" in content  # Invest currency
        
        # Should have combined totals since currencies are different
        # (Note: In our mock data, currencies are different so no combined totals)
        # But we can verify the structure exists
        currencies = set(summary.currency for summary in exporter.account_summaries.values())
        if len(currencies) == 1:
            assert "## Combined Totals" in content
        
        print("✓ Multi-account workflow test completed successfully")
    
    def test_error_recovery_workflow(self, error_prone_client, tmp_path):
        """Test workflow with API errors to verify graceful error handling."""
        exporter = PortfolioExporter({"Trading 212": error_prone_client})
        
        print("\n--- Error Recovery Workflow ---")
        
        # Should not raise exception despite API errors
        exporter.fetch_data()
        
        # Verify graceful handling
        assert "Trading 212" in exporter.account_summaries
        assert len(exporter.positions) > 0  # Portfolio fetch should still work
        
        # Check that fallbacks were used
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.free_funds == Decimal('0')  # Failed API call fallback
        
        position = exporter.positions[0]
        assert position.name == position.ticker  # Failed position details fallback
        
        # Should still be able to generate output
        markdown = exporter.generate_markdown()
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        
        # Should still be able to save file
        output_file = tmp_path / "error_recovery_test.md"
        exporter.save_to_file(str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "# Trading 212 Portfolio" in content
        
        print("✓ Error recovery workflow test completed successfully")
    
    def test_empty_portfolio_workflow(self, empty_portfolio_client, tmp_path):
        """Test workflow with empty portfolio."""
        exporter = PortfolioExporter({"Trading 212": empty_portfolio_client})
        
        print("\n--- Empty Portfolio Workflow ---")
        
        # Fetch data (should work even with empty portfolio)
        exporter.fetch_data()
        
        # Verify empty portfolio handling
        assert len(exporter.positions) == 0
        assert "Trading 212" in exporter.account_summaries
        
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.free_funds == Decimal('0.0')
        assert account_summary.invested == Decimal('0.0')
        assert account_summary.result == Decimal('0.0')
        
        # Should still generate valid markdown
        markdown = exporter.generate_markdown()
        assert isinstance(markdown, str)
        assert "# Trading 212 Portfolio" in markdown
        assert "## Portfolio Positions" in markdown
        assert "## Summary" in markdown
        
        # Should still save successfully
        output_file = tmp_path / "empty_portfolio_test.md"
        exporter.save_to_file(str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "# Trading 212 Portfolio" in content
        assert "FREE FUNDS" in content
        assert "PORTFOLIO" in content
        
        print("✓ Empty portfolio workflow test completed successfully")
    
    def test_performance_workflow_simulation(self, portfolio_exporter):
        """Test workflow performance characteristics with mocked data."""
        import time
        
        print("\n--- Performance Workflow Simulation ---")
        
        # Measure fetch time
        start_time = time.time()
        portfolio_exporter.fetch_data()
        fetch_time = time.time() - start_time
        
        # Should be fast with mocked data (< 1 second)
        assert fetch_time < 1.0, f"Fetch took too long: {fetch_time:.2f}s"
        
        # Measure markdown generation time
        start_time = time.time()
        markdown = portfolio_exporter.generate_markdown()
        generation_time = time.time() - start_time
        
        # Should be very fast (< 0.1 seconds)
        assert generation_time < 0.1, f"Generation took too long: {generation_time:.2f}s"
        
        # Verify output quality (markdown should be substantial)
        assert len(markdown) > 500, "Generated markdown should be substantial"
        
        print(f"✓ Performance test: fetch={fetch_time:.3f}s, generation={generation_time:.3f}s")
    
    def test_data_integrity_workflow(self, portfolio_exporter):
        """Test data integrity throughout the workflow."""
        print("\n--- Data Integrity Workflow ---")
        
        # Fetch data
        portfolio_exporter.fetch_data()
        
        # Store original data for comparison
        original_positions = portfolio_exporter.positions.copy()
        original_summaries = portfolio_exporter.account_summaries.copy()
        
        # Generate markdown multiple times
        markdown1 = portfolio_exporter.generate_markdown()
        markdown2 = portfolio_exporter.generate_markdown()
        
        # Data should be unchanged
        assert portfolio_exporter.positions == original_positions
        assert portfolio_exporter.account_summaries == original_summaries
        
        # Output should be consistent
        assert markdown1 == markdown2
        
        # Verify all decimal calculations maintain precision
        for position in portfolio_exporter.positions:
            # Check that decimal operations don't lose precision
            assert isinstance(position.shares, Decimal)
            assert isinstance(position.average_price, Decimal)
            assert isinstance(position.current_price, Decimal)
            assert isinstance(position.market_value, Decimal)
            assert isinstance(position.profit_loss, Decimal)
            assert isinstance(position.profit_loss_percent, Decimal)
            
            # Verify calculation accuracy
            expected_market_value = position.shares * position.current_price
            assert position.market_value == expected_market_value
            
            expected_cost_basis = position.shares * position.average_price
            assert position.cost_basis == expected_cost_basis
            
            expected_profit_loss = expected_market_value - expected_cost_basis
            assert position.profit_loss == expected_profit_loss
        
        print("✓ Data integrity workflow test completed successfully")