"""
End-to-end spot check tests for specific Trading 212 tickers.

This module validates that our exporter produces accurate results for known
positions by comparing against source of truth data from the Trading 212 app.
"""

import pytest
from decimal import Decimal

from trading212_exporter.ticker_mappings import get_display_name


@pytest.mark.e2e
class TestSpotCheckTickers:
    """Spot check validation for specific high-value tickers."""
    
    def test_ticker_name_resolution(self, source_of_truth_data):
        """Test that ticker symbols resolve to correct display names."""
        for ticker_data in source_of_truth_data["target_tickers"]:
            ticker = ticker_data["ticker"]
            expected_name = ticker_data["name"]
            
            actual_name = get_display_name(ticker)
            assert actual_name == expected_name, (
                f"Ticker {ticker} resolved to '{actual_name}', expected '{expected_name}'"
            )
    
    def test_iitu_eq_spot_check(self, e2e_exporter, source_of_truth_data, tolerance_config, validation_helpers):
        """Spot check IITU_EQ (iShares S&P 500 Information Technology Sector) against source of truth."""
        # Get reference data
        iitu_ref = next(
            ticker for ticker in source_of_truth_data["target_tickers"] 
            if ticker["ticker"] == "IITU_EQ"
        )
        
        # Fetch and find position
        e2e_exporter.fetch_data()
        iitu_position = next(
            pos for pos in e2e_exporter.positions 
            if pos.ticker == "IITU_EQ"
        )
        
        # Validate basic position data
        assert iitu_position.name == iitu_ref["name"]
        validation_helpers["assert_within_tolerance"](
            iitu_position.shares, 
            Decimal(str(iitu_ref["shares"])), 
            Decimal("0.001"), 
            "IITU_EQ shares"
        )
        
        # Validate prices (handling pence conversion)
        validation_helpers["assert_within_tolerance"](
            iitu_position.average_price,
            Decimal(str(iitu_ref["average_price_numeric"])),
            tolerance_config["price_tolerance"],
            "IITU_EQ average price"
        )
        
        validation_helpers["assert_within_tolerance"](
            iitu_position.current_price,
            Decimal(str(iitu_ref["current_price_numeric"])),
            tolerance_config["price_tolerance"],
            "IITU_EQ current price"
        )
        
        # Validate market value
        validation_helpers["assert_within_tolerance"](
            iitu_position.market_value,
            Decimal(str(iitu_ref["market_value_numeric"])),
            tolerance_config["calculation_tolerance"],
            "IITU_EQ market value"
        )
        
        # Validate profit/loss
        validation_helpers["assert_within_tolerance"](
            iitu_position.profit_loss,
            Decimal(str(iitu_ref["profit_loss_numeric"])),
            tolerance_config["calculation_tolerance"],
            "IITU_EQ profit/loss"
        )
        
        # Validate profit/loss percentage (using wider tolerance for floating-point precision)
        validation_helpers["assert_within_tolerance"](
            iitu_position.profit_loss_percent,
            Decimal(str(iitu_ref["profit_loss_percent_numeric"])),
            Decimal("0.01"),  # ±0.01% tolerance for floating-point precision
            "IITU_EQ profit/loss percentage"
        )
        
        # Validate internal calculations are consistent
        validation_helpers["validate_position_calculations"](iitu_position, iitu_ref)
        
        print(f"✓ IITU_EQ spot check passed: {iitu_position.name}")
        print(f"  Market Value: £{iitu_position.market_value}")
        print(f"  Profit/Loss: £{iitu_position.profit_loss} ({iitu_position.profit_loss_percent}%)")
    
    def test_intll_eq_spot_check(self, e2e_exporter, source_of_truth_data, tolerance_config, validation_helpers):
        """Spot check INTLl_EQ (WisdomTree Artificial Intelligence) against source of truth."""
        # Get reference data
        intl_ref = next(
            ticker for ticker in source_of_truth_data["target_tickers"] 
            if ticker["ticker"] == "INTLl_EQ"
        )
        
        # Fetch and find position
        e2e_exporter.fetch_data()
        intl_position = next(
            pos for pos in e2e_exporter.positions 
            if pos.ticker == "INTLl_EQ"
        )
        
        # Validate basic position data
        assert intl_position.name == intl_ref["name"]
        validation_helpers["assert_within_tolerance"](
            intl_position.shares,
            Decimal(str(intl_ref["shares"])),
            Decimal("0.001"),
            "INTLl_EQ shares"
        )
        
        # Validate prices
        validation_helpers["assert_within_tolerance"](
            intl_position.average_price,
            Decimal(str(intl_ref["average_price_numeric"])),
            tolerance_config["price_tolerance"],
            "INTLl_EQ average price"
        )
        
        validation_helpers["assert_within_tolerance"](
            intl_position.current_price,
            Decimal(str(intl_ref["current_price_numeric"])),
            tolerance_config["price_tolerance"],
            "INTLl_EQ current price"
        )
        
        # Validate market value
        validation_helpers["assert_within_tolerance"](
            intl_position.market_value,
            Decimal(str(intl_ref["market_value_numeric"])),
            tolerance_config["calculation_tolerance"],
            "INTLl_EQ market value"
        )
        
        # Validate profit/loss
        validation_helpers["assert_within_tolerance"](
            intl_position.profit_loss,
            Decimal(str(intl_ref["profit_loss_numeric"])),
            tolerance_config["calculation_tolerance"],
            "INTLl_EQ profit/loss"
        )
        
        # Validate profit/loss percentage (using wider tolerance for floating-point precision)
        validation_helpers["assert_within_tolerance"](
            intl_position.profit_loss_percent,
            Decimal(str(intl_ref["profit_loss_percent_numeric"])),
            Decimal("0.01"),  # ±0.01% tolerance for floating-point precision
            "INTLl_EQ profit/loss percentage"
        )
        
        # Validate internal calculations
        validation_helpers["validate_position_calculations"](intl_position, intl_ref)
        
        print(f"✓ INTLl_EQ spot check passed: {intl_position.name}")
        print(f"  Market Value: £{intl_position.market_value}")
        print(f"  Profit/Loss: £{intl_position.profit_loss} ({intl_position.profit_loss_percent}%)")
    
    def test_cnx1_eq_spot_check(self, e2e_exporter, source_of_truth_data, tolerance_config, validation_helpers):
        """Spot check CNX1_EQ (iShares NASDAQ 100) against source of truth."""
        # Get reference data
        cnx1_ref = next(
            ticker for ticker in source_of_truth_data["target_tickers"] 
            if ticker["ticker"] == "CNX1_EQ"
        )
        
        # Fetch and find position
        e2e_exporter.fetch_data()
        cnx1_position = next(
            pos for pos in e2e_exporter.positions 
            if pos.ticker == "CNX1_EQ"
        )
        
        # Validate basic position data
        assert cnx1_position.name == cnx1_ref["name"]
        validation_helpers["assert_within_tolerance"](
            cnx1_position.shares,
            Decimal(str(cnx1_ref["shares"])),
            Decimal("0.001"),
            "CNX1_EQ shares"
        )
        
        # Validate prices
        validation_helpers["assert_within_tolerance"](
            cnx1_position.average_price,
            Decimal(str(cnx1_ref["average_price_numeric"])),
            tolerance_config["price_tolerance"],
            "CNX1_EQ average price"
        )
        
        validation_helpers["assert_within_tolerance"](
            cnx1_position.current_price,
            Decimal(str(cnx1_ref["current_price_numeric"])),
            tolerance_config["price_tolerance"],
            "CNX1_EQ current price"
        )
        
        # Validate market value (note: this ticker has known discrepancies per reference data)
        validation_helpers["assert_within_tolerance"](
            cnx1_position.market_value,
            Decimal(str(cnx1_ref["market_value_numeric"])),
            Decimal("0.10"),  # Wider tolerance due to known rounding differences
            "CNX1_EQ market value"
        )
        
        # Validate profit/loss (wider tolerance due to rounding cascade)
        validation_helpers["assert_within_tolerance"](
            cnx1_position.profit_loss,
            Decimal(str(cnx1_ref["profit_loss_numeric"])),
            Decimal("0.10"),  # Wider tolerance
            "CNX1_EQ profit/loss"
        )
        
        # Validate profit/loss percentage (wider tolerance)
        validation_helpers["assert_within_tolerance"](
            cnx1_position.profit_loss_percent,
            Decimal(str(cnx1_ref["profit_loss_percent_numeric"])),
            Decimal("0.01"),  # ±0.01% tolerance
            "CNX1_EQ profit/loss percentage"
        )
        
        # Validate internal calculations
        validation_helpers["validate_position_calculations"](cnx1_position, cnx1_ref)
        
        print(f"✓ CNX1_EQ spot check passed: {cnx1_position.name}")
        print(f"  Market Value: £{cnx1_position.market_value}")
        print(f"  Profit/Loss: £{cnx1_position.profit_loss} ({cnx1_position.profit_loss_percent}%)")
        print("  Note: This ticker has known minor rounding discrepancies with the app")
    
    def test_all_target_tickers_present(self, e2e_exporter, source_of_truth_data):
        """Ensure all target tickers are present in the portfolio."""
        e2e_exporter.fetch_data()
        
        portfolio_tickers = {pos.ticker for pos in e2e_exporter.positions}
        target_tickers = {ticker["ticker"] for ticker in source_of_truth_data["target_tickers"]}
        
        missing_tickers = target_tickers - portfolio_tickers
        assert not missing_tickers, f"Missing target tickers: {missing_tickers}"
        
        print(f"✓ All {len(target_tickers)} target tickers present in portfolio")
    
    def test_spot_check_comprehensive_validation(self, e2e_exporter, source_of_truth_data, tolerance_config):
        """Comprehensive validation of all target tickers in a single test."""
        e2e_exporter.fetch_data()
        
        total_market_value = Decimal('0')
        total_profit_loss = Decimal('0')
        
        for ticker_ref in source_of_truth_data["target_tickers"]:
            ticker = ticker_ref["ticker"]
            
            # Find position
            position = next(
                (pos for pos in e2e_exporter.positions if pos.ticker == ticker),
                None
            )
            assert position is not None, f"Position not found for ticker {ticker}"
            
            # Accumulate totals
            total_market_value += position.market_value
            total_profit_loss += position.profit_loss
            
            # Validate key metrics are reasonable
            assert position.market_value > 0, f"{ticker} market value should be positive"
            assert position.shares > 0, f"{ticker} shares should be positive"
            assert position.current_price > 0, f"{ticker} current price should be positive"
            assert position.average_price > 0, f"{ticker} average price should be positive"
            
            print(f"✓ {ticker} ({position.name}): £{position.market_value} "
                  f"({'+' if position.profit_loss >= 0 else ''}£{position.profit_loss})")
        
        # Validate totals are reasonable
        assert total_market_value > Decimal('1000'), "Total market value should be substantial"
        assert total_profit_loss > Decimal('100'), "Total profit should be positive and substantial"
        
        print(f"\n✓ Comprehensive validation complete:")
        print(f"  Total Market Value: £{total_market_value}")
        print(f"  Total Profit/Loss: £{total_profit_loss}")
        print(f"  Tickers Validated: {len(source_of_truth_data['target_tickers'])}")
    
    def test_currency_and_formatting_consistency(self, e2e_exporter, source_of_truth_data):
        """Test currency handling and formatting consistency."""
        e2e_exporter.fetch_data()
        
        # Generate markdown to test formatting
        markdown = e2e_exporter.generate_markdown()
        
        # Check that all target tickers appear in the markdown
        for ticker_ref in source_of_truth_data["target_tickers"]:
            ticker = ticker_ref["ticker"] 
            name = ticker_ref["name"]
            
            assert name in markdown, f"Ticker name '{name}' not found in markdown output"
            
            # Check for GBP currency symbol
            assert "£" in markdown, "GBP currency symbol not found in markdown"
        
        # Validate currency consistency in positions
        for position in e2e_exporter.positions:
            if position.ticker in [t["ticker"] for t in source_of_truth_data["target_tickers"]]:
                assert position.currency == "GBP", f"{position.ticker} should be in GBP"
        
        print("✓ Currency and formatting consistency validated")
        print(f"  Markdown length: {len(markdown)} characters")
        print(f"  Contains GBP symbols: {'£' in markdown}")
        
    @pytest.mark.slow
    def test_spot_check_performance_benchmark(self, e2e_exporter):
        """Benchmark performance of spot check operations."""
        import time
        
        # Measure fetch time
        start_time = time.time()
        e2e_exporter.fetch_data()
        fetch_time = time.time() - start_time
        
        # Measure markdown generation time
        start_time = time.time()
        markdown = e2e_exporter.generate_markdown()
        generation_time = time.time() - start_time
        
        # Measure file save time
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            start_time = time.time()
            e2e_exporter.save_to_file(f.name)
            save_time = time.time() - start_time
        
        # Performance assertions (generous thresholds for e2e tests)
        assert fetch_time < 2.0, f"Fetch time too slow: {fetch_time:.2f}s"
        assert generation_time < 1.0, f"Generation time too slow: {generation_time:.2f}s"
        assert save_time < 1.0, f"Save time too slow: {save_time:.2f}s"
        
        total_time = fetch_time + generation_time + save_time
        
        print(f"✓ Performance benchmark complete:")
        print(f"  Fetch: {fetch_time:.3f}s")
        print(f"  Generation: {generation_time:.3f}s") 
        print(f"  Save: {save_time:.3f}s")
        print(f"  Total: {total_time:.3f}s")
        print(f"  Markdown size: {len(markdown)} chars")