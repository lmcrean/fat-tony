"""
Comprehensive end-to-end workflow tests for Trading 212 portfolio exporter.

These tests validate complete user scenarios from API data fetching through
final markdown generation and file output, using realistic data patterns.
"""

import pytest
import tempfile
import time
import os
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch
from dotenv import load_dotenv

from trading212_exporter import Trading212Client, PortfolioExporter


@pytest.mark.e2e
class TestE2EWorkflow:
    """End-to-end workflow validation tests."""
    
    def test_complete_export_workflow(self, e2e_exporter, source_of_truth_data, tmp_path):
        """Test the complete workflow from data fetch to file export."""
        print("\n=== Complete E2E Workflow Test ===")
        
        # Step 1: Data Fetching
        print("Step 1: Fetching portfolio data...")
        e2e_exporter.fetch_data()
        
        # Verify data was fetched
        assert len(e2e_exporter.positions) == len(source_of_truth_data["target_tickers"])
        assert len(e2e_exporter.account_summaries) == 1
        assert "Trading 212" in e2e_exporter.account_summaries
        
        # Step 2: Data Validation
        print("Step 2: Validating fetched data...")
        for position in e2e_exporter.positions:
            assert hasattr(position, 'ticker')
            assert hasattr(position, 'name')
            assert hasattr(position, 'shares')
            assert hasattr(position, 'market_value')
            assert hasattr(position, 'profit_loss')
            assert hasattr(position, 'profit_loss_percent')
            
            # Verify all values are reasonable
            assert position.shares > 0
            assert position.market_value > 0
            assert position.current_price > 0
            assert position.average_price > 0
        
        # Step 3: Account Summary Validation
        print("Step 3: Validating account summary...")
        account = e2e_exporter.account_summaries["Trading 212"]
        assert account.free_funds >= 0
        assert account.invested > 0
        assert account.currency == "GBP"
        
        # Step 4: Markdown Generation
        print("Step 4: Generating markdown output...")
        markdown_content = e2e_exporter.generate_markdown()
        
        assert isinstance(markdown_content, str)
        assert len(markdown_content) > 1000  # Should be substantial
        assert "# Trading 212 Portfolio" in markdown_content
        assert "Generated on" in markdown_content
        
        # Step 5: File Export
        print("Step 5: Exporting to file...")
        output_file = tmp_path / "e2e_workflow_test.md"
        e2e_exporter.save_to_file(str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Step 6: File Content Verification
        print("Step 6: Verifying file content...")
        file_content = output_file.read_text(encoding='utf-8')
        assert file_content == markdown_content
        
        # Verify specific content requirements
        for ticker_data in source_of_truth_data["target_tickers"]:
            assert ticker_data["name"] in file_content
        
        # Verify table structure
        assert "|" in file_content  # Table formatting
        assert "NAME" in file_content
        assert "SHARES" in file_content
        assert "MARKET VALUE" in file_content
        assert "RESULT" in file_content
        
        print("✓ Complete E2E workflow test passed")
        print(f"  Output file: {output_file}")
        print(f"  File size: {output_file.stat().st_size} bytes")
        print(f"  Positions: {len(e2e_exporter.positions)}")
    
    def test_error_resilience_workflow(self, source_of_truth_data, tmp_path):
        """Test workflow resilience to API errors and partial failures."""
        print("\n=== Error Resilience Workflow Test ===")
        
        # Create a client that fails on some calls
        error_client = Mock(spec=Trading212Client)
        
        # Successful portfolio call
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
        error_client.get_portfolio.return_value = positions_data
        
        # Failed account cash call
        error_client.get_account_cash.side_effect = Exception("API Error")
        
        # Failed metadata call
        error_client.get_account_metadata.side_effect = Exception("API Error")
        
        # Successful position details for first ticker, fail for others
        def mock_position_details(ticker):
            if ticker == source_of_truth_data["target_tickers"][0]["ticker"]:
                return {"name": source_of_truth_data["target_tickers"][0]["name"]}
            raise Exception("API Error")
        error_client.get_position_details.side_effect = mock_position_details
        
        # Create exporter with error-prone client
        exporter = PortfolioExporter({"Trading 212": error_client})
        
        print("Testing data fetch with partial API failures...")
        
        # Should not raise exception
        exporter.fetch_data()
        
        # Should still have positions (portfolio call succeeded)
        assert len(exporter.positions) > 0
        
        # Should have fallback values for failed calls
        account = exporter.account_summaries["Trading 212"]
        assert account.free_funds == Decimal('0')  # Fallback value
        
        # First position should have name, others should use ticker
        first_position = next(
            pos for pos in exporter.positions 
            if pos.ticker == source_of_truth_data["target_tickers"][0]["ticker"]
        )
        assert first_position.name == source_of_truth_data["target_tickers"][0]["name"]
        
        # Should still be able to generate markdown
        markdown_content = exporter.generate_markdown()
        assert isinstance(markdown_content, str)
        assert len(markdown_content) > 0
        
        # Should still be able to save file
        output_file = tmp_path / "error_resilience_test.md"
        exporter.save_to_file(str(output_file))
        assert output_file.exists()
        
        print("✓ Error resilience workflow test passed")
        print(f"  Handled partial API failures gracefully")
        print(f"  Generated output despite errors")
    
    def test_large_portfolio_workflow(self, tmp_path):
        """Test workflow with a larger, more realistic portfolio size."""
        print("\n=== Large Portfolio Workflow Test ===")
        
        # Create a client with many positions
        large_client = Mock(spec=Trading212Client)
        
        # Generate 50 positions
        positions_data = []
        expected_names = {}
        
        for i in range(50):
            ticker = f"TEST{i:02d}_US_EQ"
            name = f"Test Company {i:02d}"
            
            positions_data.append({
                "ticker": ticker,
                "quantity": float(10 + i),
                "averagePrice": float(100 + i * 5),
                "currentPrice": float(120 + i * 6),
                "ppl": float((120 + i * 6 - 100 - i * 5) * (10 + i)),
                "fxPpl": 0.0,
                "pieQuantity": 0.0
            })
            expected_names[ticker] = name
        
        large_client.get_portfolio.return_value = positions_data
        
        # Mock account cash
        large_client.get_account_cash.return_value = {
            "free": 10000.0,
            "invested": sum(pos["quantity"] * pos["currentPrice"] for pos in positions_data),
            "result": sum(pos["ppl"] for pos in positions_data),
            "currency": "USD"
        }
        
        # Mock account metadata
        large_client.get_account_metadata.return_value = {
            "accountType": "INVEST",
            "currency": "USD"
        }
        
        # Mock position details
        def mock_position_details(ticker):
            return {"name": expected_names.get(ticker, ticker)}
        large_client.get_position_details.side_effect = mock_position_details
        
        # Create exporter
        exporter = PortfolioExporter({"Trading 212": large_client})
        
        print(f"Testing workflow with {len(positions_data)} positions...")
        
        # Measure performance
        start_time = time.time()
        exporter.fetch_data()
        fetch_time = time.time() - start_time
        
        start_time = time.time()
        markdown_content = exporter.generate_markdown()
        generation_time = time.time() - start_time
        
        start_time = time.time()
        output_file = tmp_path / "large_portfolio_test.md"
        exporter.save_to_file(str(output_file))
        save_time = time.time() - start_time
        
        # Validate results
        assert len(exporter.positions) == 50
        assert len(markdown_content) > 10000  # Should be substantial
        assert output_file.exists()
        
        # Performance should be reasonable even with large portfolio
        total_time = fetch_time + generation_time + save_time
        assert total_time < 5.0, f"Large portfolio processing too slow: {total_time:.2f}s"
        
        print("✓ Large portfolio workflow test passed")
        print(f"  Positions: {len(exporter.positions)}")
        print(f"  Fetch time: {fetch_time:.3f}s")
        print(f"  Generation time: {generation_time:.3f}s")
        print(f"  Save time: {save_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Output size: {len(markdown_content)} chars")
    
    def test_multi_account_e2e_workflow(self, source_of_truth_data, tmp_path):
        """Test end-to-end workflow with multiple Trading 212 accounts."""
        print("\n=== Multi-Account E2E Workflow Test ===")
        
        # Create two clients for different account types
        isa_client = Mock(spec=Trading212Client)
        invest_client = Mock(spec=Trading212Client)
        
        # ISA account positions (first two tickers)
        isa_positions = []
        for ticker_data in source_of_truth_data["target_tickers"][:2]:
            isa_positions.append({
                "ticker": ticker_data["ticker"],
                "quantity": ticker_data["shares"],
                "averagePrice": ticker_data["average_price_numeric"],
                "currentPrice": ticker_data["current_price_numeric"],
                "ppl": ticker_data["profit_loss_numeric"],
                "fxPpl": 0.0,
                "pieQuantity": 0.0
            })
        
        # Invest account positions (last ticker)
        invest_positions = []
        ticker_data = source_of_truth_data["target_tickers"][2]
        invest_positions.append({
            "ticker": ticker_data["ticker"],
            "quantity": ticker_data["shares"],
            "averagePrice": ticker_data["average_price_numeric"],
            "currentPrice": ticker_data["current_price_numeric"],
            "ppl": ticker_data["profit_loss_numeric"],
            "fxPpl": 0.0,
            "pieQuantity": 0.0
        })
        
        # Configure ISA client
        isa_client.get_portfolio.return_value = isa_positions
        isa_client.get_account_cash.return_value = {
            "free": 500.0,
            "invested": sum(pos["quantity"] * pos["currentPrice"] for pos in isa_positions),
            "result": sum(pos["ppl"] for pos in isa_positions),
            "currency": "GBP"
        }
        isa_client.get_account_metadata.return_value = {
            "accountType": "ISA",
            "currency": "GBP"
        }
        
        # Configure Invest client
        invest_client.get_portfolio.return_value = invest_positions
        invest_client.get_account_cash.return_value = {
            "free": 1000.0,
            "invested": sum(pos["quantity"] * pos["currentPrice"] for pos in invest_positions),
            "result": sum(pos["ppl"] for pos in invest_positions),
            "currency": "GBP"
        }
        invest_client.get_account_metadata.return_value = {
            "accountType": "INVEST",
            "currency": "GBP"
        }
        
        # Mock position details for both clients
        def mock_isa_position_details(ticker):
            for t in source_of_truth_data["target_tickers"][:2]:
                if t["ticker"] == ticker:
                    return {"name": t["name"]}
            return {"name": ticker}
        
        def mock_invest_position_details(ticker):
            t = source_of_truth_data["target_tickers"][2]
            if t["ticker"] == ticker:
                return {"name": t["name"]}
            return {"name": ticker}
        
        isa_client.get_position_details.side_effect = mock_isa_position_details
        invest_client.get_position_details.side_effect = mock_invest_position_details
        
        # Create multi-account exporter
        exporter = PortfolioExporter({
            "Stocks & Shares ISA": isa_client,
            "Invest Account": invest_client
        })
        
        print("Testing multi-account data fetch...")
        exporter.fetch_data()
        
        # Validate multi-account structure
        assert len(exporter.account_summaries) == 2
        assert "Stocks & Shares ISA" in exporter.account_summaries
        assert "Invest Account" in exporter.account_summaries
        
        # Validate positions are attributed to correct accounts
        for position in exporter.positions:
            assert hasattr(position, 'account_name')
            assert position.account_name in ["Stocks & Shares ISA", "Invest Account"]
        
        # Test markdown generation
        print("Generating multi-account markdown...")
        markdown_content = exporter.generate_markdown()
        
        # Should contain both account sections
        assert "## Stocks & Shares ISA" in markdown_content
        assert "## Invest Account" in markdown_content
        
        # Test file export
        output_file = tmp_path / "multi_account_e2e_test.md"
        exporter.save_to_file(str(output_file))
        
        assert output_file.exists()
        file_content = output_file.read_text(encoding='utf-8')
        assert file_content == markdown_content
        
        print("✓ Multi-account E2E workflow test passed")
        print(f"  Accounts: {len(exporter.account_summaries)}")
        print(f"  Total positions: {len(exporter.positions)}")
        print(f"  Output file: {output_file}")
    
    def test_empty_portfolio_e2e_workflow(self, tmp_path):
        """Test workflow with completely empty portfolio."""
        print("\n=== Empty Portfolio E2E Workflow Test ===")
        
        empty_client = Mock(spec=Trading212Client)
        
        # Empty portfolio
        empty_client.get_portfolio.return_value = []
        
        # Zero balances
        empty_client.get_account_cash.return_value = {
            "free": 0.0,
            "invested": 0.0,
            "result": 0.0,
            "currency": "GBP"
        }
        
        empty_client.get_account_metadata.return_value = {
            "accountType": "INVEST",
            "currency": "GBP"
        }
        
        # No position details needed
        empty_client.get_position_details.return_value = {"name": ""}
        
        exporter = PortfolioExporter({"Trading 212": empty_client})
        
        print("Testing empty portfolio workflow...")
        
        # Should handle empty portfolio gracefully
        exporter.fetch_data()
        
        assert len(exporter.positions) == 0
        assert len(exporter.account_summaries) == 1
        
        account = exporter.account_summaries["Trading 212"]
        assert account.free_funds == Decimal('0')
        assert account.invested == Decimal('0')
        assert account.result == Decimal('0')
        
        # Should still generate valid markdown
        markdown_content = exporter.generate_markdown()
        assert isinstance(markdown_content, str)
        assert "# Trading 212 Portfolio" in markdown_content
        assert "No positions" in markdown_content or "FREE FUNDS" in markdown_content
        
        # Should save successfully
        output_file = tmp_path / "empty_portfolio_e2e_test.md"
        exporter.save_to_file(str(output_file))
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        print("✓ Empty portfolio E2E workflow test passed")
        print(f"  Generated valid output for empty portfolio")
        print(f"  Output size: {len(markdown_content)} chars")
    
    @pytest.mark.slow
    def test_performance_benchmark_e2e(self, e2e_exporter):
        """Comprehensive performance benchmark of the complete workflow."""
        print("\n=== Performance Benchmark E2E Test ===")
        
        # Multiple iterations to get consistent measurements
        iterations = 5
        fetch_times = []
        generation_times = []
        
        for i in range(iterations):
            # Fresh exporter instance for each iteration
            exporter = PortfolioExporter(e2e_exporter.clients)
            
            # Measure fetch
            start_time = time.time()
            exporter.fetch_data()
            fetch_times.append(time.time() - start_time)
            
            # Measure generation
            start_time = time.time()
            markdown = exporter.generate_markdown()
            generation_times.append(time.time() - start_time)
        
        # Calculate averages
        avg_fetch = sum(fetch_times) / len(fetch_times)
        avg_generation = sum(generation_times) / len(generation_times)
        avg_total = avg_fetch + avg_generation
        
        # Performance thresholds
        assert avg_fetch < 1.0, f"Average fetch time too slow: {avg_fetch:.3f}s"
        assert avg_generation < 0.5, f"Average generation time too slow: {avg_generation:.3f}s"
        assert avg_total < 1.5, f"Average total time too slow: {avg_total:.3f}s"
        
        print("✓ Performance benchmark E2E test passed")
        print(f"  Iterations: {iterations}")
        print(f"  Avg fetch time: {avg_fetch:.3f}s")
        print(f"  Avg generation time: {avg_generation:.3f}s")
        print(f"  Avg total time: {avg_total:.3f}s")
        print(f"  Fetch time range: {min(fetch_times):.3f}s - {max(fetch_times):.3f}s")
        print(f"  Generation time range: {min(generation_times):.3f}s - {max(generation_times):.3f}s")
    
    def test_totals_spot_check(self, tmp_path):
        """Test account totals against reference data from e2e/.env file."""
        print("\n=== Totals Spot Check Test ===")
        
        # Load e2e test configuration
        e2e_env_path = Path(__file__).parent / ".env"
        if not e2e_env_path.exists():
            pytest.skip(f"E2E test data not found at {e2e_env_path}. Create e2e/.env with test values.")
        
        load_dotenv(e2e_env_path)
        
        # Load reference data from environment
        t212_cash_min = Decimal(os.getenv("T212_CASH_MIN", "0"))
        t212_cash_max = Decimal(os.getenv("T212_CASH_MAX", "10"))
        t212_investments = Decimal(os.getenv("T212_INVESTMENTS", "8450.0"))
        
        isa_cash = Decimal(os.getenv("ISA_CASH", "7128.0"))
        isa_investments = Decimal(os.getenv("ISA_INVESTMENTS", "6801.0"))
        
        combined_investments = Decimal(os.getenv("COMBINED_INVESTMENTS", "15251.0"))
        combined_cash_min = Decimal(os.getenv("COMBINED_CASH_MIN", "7128.0"))
        combined_cash_max = Decimal(os.getenv("COMBINED_CASH_MAX", "7138.0"))
        
        # Account names
        t212_account_name = os.getenv("T212_ACCOUNT_NAME", "T212 Account")
        isa_account_name = os.getenv("ISA_ACCOUNT_NAME", "Stocks & Shares ISA")
        default_currency = os.getenv("DEFAULT_CURRENCY", "GBP")
        
        # Dummy position data
        t212_dummy_ticker = os.getenv("T212_DUMMY_TICKER", "DUMMY_T212_EQ")
        t212_dummy_shares = float(os.getenv("T212_DUMMY_SHARES", "100.0"))
        t212_dummy_avg_price = float(os.getenv("T212_DUMMY_AVG_PRICE", "84.50"))
        t212_dummy_name = os.getenv("T212_DUMMY_NAME", "Dummy T212 Position")
        
        isa_dummy_ticker = os.getenv("ISA_DUMMY_TICKER", "DUMMY_ISA_EQ")
        isa_dummy_shares = float(os.getenv("ISA_DUMMY_SHARES", "100.0"))
        isa_dummy_avg_price = float(os.getenv("ISA_DUMMY_AVG_PRICE", "68.01"))
        isa_dummy_name = os.getenv("ISA_DUMMY_NAME", "Dummy ISA Position")
        
        print(f"Reference data loaded from {e2e_env_path}")
        print(f"Expected - {t212_account_name}: Cash £{t212_cash_min}-{t212_cash_max}, Investments £{t212_investments}")
        print(f"Expected - {isa_account_name}: Cash £{isa_cash}, Investments £{isa_investments}")
        
        # Create T212 Account client
        t212_client = Mock(spec=Trading212Client)
        t212_client.get_portfolio.return_value = [
            {
                "ticker": t212_dummy_ticker,
                "quantity": t212_dummy_shares,
                "averagePrice": t212_dummy_avg_price,
                "currentPrice": t212_dummy_avg_price,  # No profit/loss for simplicity
                "ppl": 0.0,
                "fxPpl": 0.0,
                "pieQuantity": 0.0
            }
        ]
        # Use midpoint of cash range for test
        t212_test_cash = float((t212_cash_min + t212_cash_max) / 2)
        t212_client.get_account_cash.return_value = {
            "free": t212_test_cash,
            "invested": float(t212_investments),
            "result": 0.0,
            "currency": default_currency
        }
        t212_client.get_account_metadata.return_value = {
            "accountType": "INVEST",
            "currency": default_currency
        }
        t212_client.get_position_details.return_value = {"name": t212_dummy_name}
        
        # Create ISA client
        isa_client = Mock(spec=Trading212Client)
        isa_client.get_portfolio.return_value = [
            {
                "ticker": isa_dummy_ticker,
                "quantity": isa_dummy_shares,
                "averagePrice": isa_dummy_avg_price,
                "currentPrice": isa_dummy_avg_price,  # No profit/loss for simplicity
                "ppl": 0.0,
                "fxPpl": 0.0,
                "pieQuantity": 0.0
            }
        ]
        isa_client.get_account_cash.return_value = {
            "free": float(isa_cash),
            "invested": float(isa_investments),
            "result": 0.0,
            "currency": default_currency
        }
        isa_client.get_account_metadata.return_value = {
            "accountType": "ISA",
            "currency": default_currency
        }
        isa_client.get_position_details.return_value = {"name": isa_dummy_name}
        
        # Create multi-account exporter
        exporter = PortfolioExporter({
            t212_account_name: t212_client,
            isa_account_name: isa_client
        })
        
        print("Testing totals against reference data...")
        exporter.fetch_data()
        
        # Validate account summaries
        assert len(exporter.account_summaries) == 2
        assert t212_account_name in exporter.account_summaries
        assert isa_account_name in exporter.account_summaries
        
        # Validate T212 Account totals
        t212_account = exporter.account_summaries[t212_account_name]
        print(f"{t212_account_name} - Cash: £{t212_account.free_funds}, Investments: £{t212_account.invested}")
        
        # Cash should be within expected range
        assert t212_cash_min <= t212_account.free_funds <= t212_cash_max, \
            f"{t212_account_name} cash £{t212_account.free_funds} not in expected range £{t212_cash_min}-{t212_cash_max}"
        
        # Investments should match exactly
        assert t212_account.invested == t212_investments, \
            f"{t212_account_name} investments £{t212_account.invested} != expected £{t212_investments}"
        
        # Validate ISA totals
        isa_account = exporter.account_summaries[isa_account_name]
        print(f"{isa_account_name} - Cash: £{isa_account.free_funds}, Investments: £{isa_account.invested}")
        
        assert isa_account.free_funds == isa_cash, \
            f"{isa_account_name} cash £{isa_account.free_funds} != expected £{isa_cash}"
        
        assert isa_account.invested == isa_investments, \
            f"{isa_account_name} investments £{isa_account.invested} != expected £{isa_investments}"
        
        # Validate combined totals
        total_investments = t212_account.invested + isa_account.invested
        total_cash = t212_account.free_funds + isa_account.free_funds
        
        print(f"Combined - Cash: £{total_cash}, Investments: £{total_investments}")
        
        assert total_investments == combined_investments, \
            f"Combined investments £{total_investments} != expected £{combined_investments}"
        
        # Combined cash should be within expected range
        assert combined_cash_min <= total_cash <= combined_cash_max, \
            f"Combined cash £{total_cash} not in expected range £{combined_cash_min}-{combined_cash_max}"
        
        print("✓ Totals spot check test passed")
        print(f"  {t212_account_name}: Cash £{t212_account.free_funds}, Investments £{t212_account.invested}")
        print(f"  {isa_account_name}: Cash £{isa_account.free_funds}, Investments £{isa_account.invested}")
        print(f"  Combined: Cash £{total_cash}, Investments £{total_investments}")
        print(f"  All totals match reference data from e2e/.env")