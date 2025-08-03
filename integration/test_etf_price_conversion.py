#!/usr/bin/env python3
"""
Comprehensive test suite for ETF price conversion fixes.
Tests all problematic tickers identified in the discrepancy analysis.
"""

import sys
import pytest
from decimal import Decimal
from typing import Dict, Tuple

# Add the trading212_exporter to the path
sys.path.insert(0, 'trading212_exporter')

from trading212_exporter.exporter import PortfolioExporter


class TestETFPriceConversion:
    """Test ETF price conversion logic for all problematic tickers."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create a mock exporter instance to test the conversion methods
        self.exporter = PortfolioExporter({})
    
    def test_known_pence_tickers_detection(self):
        """Test that all problematic ETF tickers are detected as pence-priced."""
        
        # Test cases: (ticker, sample_price, should_convert, description)
        test_cases = [
            # Originally confirmed pence-priced ETFs
            ('IITU_EQ', Decimal('2827.0'), True, 'iShares S&P 500 IT'),
            ('INTLl_EQ', Decimal('5557.5'), True, 'WisdomTree AI'),
            ('SGLNl_EQ', Decimal('4910.0'), True, 'iShares Physical Gold'),
            ('CNX1_EQ', Decimal('98520.0'), True, 'iShares NASDAQ 100'),
            
            # Newly added ETFs from discrepancy analysis
            ('VUAGl_EQ', Decimal('8998.0'), True, 'Vanguard S&P 500 (Acc) - ISA'),
            # Note: R1GRl_EQ removed - it's actually a USD ETF, not pence-priced
            ('VGERl_EQ', Decimal('2943.0'), True, 'Vanguard Germany All Cap'),
            ('SMGBl_EQ', Decimal('3553.0'), True, 'VanEck Semiconductor (Acc)'),
            ('VWRPl_EQ', Decimal('11508.0'), True, 'Vanguard FTSE All-World (Acc)'),
            ('RBODl_EQ', Decimal('994.7'), True, 'iShares Automation & Robotics (Dist)'),
            ('IINDl_EQ', Decimal('713.4'), True, 'iShares MSCI India (Acc)'),
            ('FXACa_EQ', Decimal('415.25'), True, 'iShares China Large Cap (Acc)'),
            ('EXICd_EQ', Decimal('684.1'), True, 'iShares Core DAX DE (Dist)'),
            
            # Control cases - should NOT be converted
            ('NVDA_US_EQ', Decimal('173.03'), False, 'Nvidia (US stock)'),
            ('PLTR_US_EQ', Decimal('154.87'), False, 'Palantir (US stock)'),
            ('GOOGL_US_EQ', Decimal('188.89'), False, 'Alphabet (US stock)'),
            ('R1GRl_EQ', Decimal('40.32'), False, 'iShares Russell 1000 Growth (USD ETF)'),
            ('RMVl_EQ', Decimal('812.2'), False, 'Rightmove (UK stock in pounds)'),
        ]
        
        print("\n=== Testing ETF Price Conversion Detection ===")
        for ticker, price, should_convert, description in test_cases:
            result = self.exporter._is_uk_etf_priced_in_pence(ticker, price)
            print(f"{ticker:12} | {price:>8} | {should_convert!s:>7} | {result!s:>7} | {description}")
            
            assert result == should_convert, (
                f"Failed for {ticker} ({description}): "
                f"expected {should_convert}, got {result}"
            )
        
        print("All ETF price conversion detection tests passed!")
    
    def test_pence_to_pounds_conversion(self):
        """Test the actual pence to pounds conversion calculations."""
        
        conversion_tests = [
            # (pence_value, expected_pounds_value)
            (Decimal('2827.0'), Decimal('28.27')),
            (Decimal('5557.5'), Decimal('55.575')),  # Note: keeps precision
            (Decimal('98520.0'), Decimal('985.20')),
            (Decimal('8998.0'), Decimal('89.98')),
            (Decimal('100'), Decimal('1.00')),
            (Decimal('50'), Decimal('0.50')),
            (Decimal('1'), Decimal('0.01')),
        ]
        
        print("\n=== Testing Pence to Pounds Conversion ===")
        for pence, expected_pounds in conversion_tests:
            result = self.exporter._convert_pence_to_pounds(pence)
            print(f"p{pence} -> £{result} (expected £{expected_pounds})")
            
            assert result == expected_pounds, (
                f"Conversion failed: p{pence} should be £{expected_pounds}, got £{result}"
            )
        
        print("All pence to pounds conversion tests passed!")
    
    def test_market_value_calculations(self):
        """Test that market value calculations work correctly after price conversion."""
        
        # Test cases with real problematic data from discrepancy analysis
        test_positions = [
            {
                'ticker': 'VUAGl_EQ',
                'name': 'Vanguard S&P 500 (Acc)',
                'shares': Decimal('34.8374'),
                'raw_current_price': Decimal('8998.0'),  # In pence
                'expected_current_price': Decimal('89.98'),  # In pounds
                'expected_market_value': Decimal('3134.67'),  # shares * converted_price
            },
            {
                'ticker': 'SMGBl_EQ',
                'name': 'VanEck Semiconductor (Acc)',
                'shares': Decimal('6.45'),
                'raw_current_price': Decimal('3553.0'),  # In pence
                'expected_current_price': Decimal('35.53'),  # In pounds
                'expected_market_value': Decimal('229.17'),  # shares * converted_price
            },
            # Note: R1GRl_EQ test removed - it's actually a USD ETF, not pence-priced
        ]
        
        print("\n=== Testing Market Value Calculations After Price Conversion ===")
        for position in test_positions:
            # Test price conversion
            should_convert = self.exporter._is_uk_etf_priced_in_pence(
                position['ticker'], 
                position['raw_current_price']
            )
            assert should_convert, f"{position['ticker']} should be detected as pence-priced"
            
            # Test price conversion
            converted_price = self.exporter._convert_pence_to_pounds(position['raw_current_price'])
            assert converted_price == position['expected_current_price'], (
                f"{position['ticker']}: price conversion failed. "
                f"Expected £{position['expected_current_price']}, got £{converted_price}"
            )
            
            # Test market value calculation
            calculated_market_value = position['shares'] * converted_price
            # Round to 2 decimal places for comparison
            calculated_market_value = calculated_market_value.quantize(Decimal('0.01'))
            
            print(f"{position['ticker']:12} | {position['shares']:>8} shares × £{converted_price:>6} = £{calculated_market_value:>8}")
            
            assert calculated_market_value == position['expected_market_value'], (
                f"{position['ticker']}: market value calculation failed. "
                f"Expected £{position['expected_market_value']}, got £{calculated_market_value}"
            )
        
        print("All market value calculation tests passed!")
    
    def test_no_conversion_for_us_stocks(self):
        """Test that US stocks are never converted."""
        
        us_stocks = [
            ('NVDA_US_EQ', Decimal('173.03')),
            ('PLTR_US_EQ', Decimal('154.87')),
            ('GOOGL_US_EQ', Decimal('188.89')),
            ('META_US_EQ', Decimal('749.59')),
            ('AMZN_US_EQ', Decimal('215.10')),
        ]
        
        print("\n=== Testing US Stocks Are Not Converted ===")
        for ticker, price in us_stocks:
            should_convert = self.exporter._is_uk_etf_priced_in_pence(ticker, price)
            print(f"{ticker:12} | £{price:>8} | Should convert: {should_convert}")
            
            assert not should_convert, f"US stock {ticker} should not be converted"
        
        print("All US stock tests passed!")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        
        edge_cases = [
            # Very small prices
            ('VUAGl_EQ', Decimal('0.01'), True),
            ('VUAGl_EQ', Decimal('1.00'), True),
            
            # Very large prices
            ('CNX1_EQ', Decimal('999999.99'), True),
            
            # Zero price (should not crash)
            ('VUAGl_EQ', Decimal('0'), True),
            
            # Negative price (should not crash)
            ('VUAGl_EQ', Decimal('-100'), True),
        ]
        
        print("\n=== Testing Edge Cases ===")
        for ticker, price, expected in edge_cases:
            try:
                result = self.exporter._is_uk_etf_priced_in_pence(ticker, price)
                conversion_result = self.exporter._convert_pence_to_pounds(price)
                print(f"{ticker:12} | {price:>8} | Convert: {result} | Result: £{conversion_result}")
                
                assert result == expected, f"Edge case failed for {ticker} with price {price}"
                
            except Exception as e:
                print(f"ERROR: {ticker} with price {price} caused exception: {e}")
                raise
        
        print("All edge case tests passed!")


def run_comprehensive_tests():
    """Run all ETF price conversion tests."""
    print("Running Comprehensive ETF Price Conversion Tests")
    print("=" * 60)
    
    test_instance = TestETFPriceConversion()
    test_instance.setup_method()
    
    try:
        test_instance.test_known_pence_tickers_detection()
        test_instance.test_pence_to_pounds_conversion()
        test_instance.test_market_value_calculations()
        test_instance.test_no_conversion_for_us_stocks()
        test_instance.test_edge_cases()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ETF price conversion fixes are working correctly.")
        print("The £1,354.17 portfolio discrepancy should now be resolved.")
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_comprehensive_tests()