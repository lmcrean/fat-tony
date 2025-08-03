#!/usr/bin/env python3
"""
Verify that the ETF price conversion fix correctly identifies and converts problematic tickers.
"""

import sys
from decimal import Decimal

# Add the trading212_exporter to the path
sys.path.insert(0, 'trading212_exporter')

from trading212_exporter.exporter import PortfolioExporter

def verify_conversion_logic():
    """Verify the conversion logic works for problematic ETFs."""
    
    print("Verifying ETF Price Conversion Fix")
    print("=" * 60)
    
    # Create exporter instance
    exporter = PortfolioExporter({})
    
    # Test cases based on the analysis - assuming API returns prices in pence
    problematic_etfs = [
        {
            'ticker': 'VUAGl_EQ',
            'name': 'Vanguard S&P 500 (Acc)',
            'api_price_pence': Decimal('8998.0'),  # API returns in pence
            'expected_pounds': Decimal('89.98'),    # Should convert to pounds
            'shares': Decimal('34.8374'),
            'expected_market_value': Decimal('3134.67')
        },
        {
            'ticker': 'VGERl_EQ',
            'name': 'Vanguard Germany All Cap',
            'api_price_pence': Decimal('2943.0'),
            'expected_pounds': Decimal('29.43'),
            'shares': Decimal('11.2'),
            'expected_market_value': Decimal('329.62')
        },
        {
            'ticker': 'SMGBl_EQ',
            'name': 'VanEck Semiconductor (Acc)',
            'api_price_pence': Decimal('3553.0'),
            'expected_pounds': Decimal('35.53'),
            'shares': Decimal('6.45'),
            'expected_market_value': Decimal('229.17')
        }
    ]
    
    print("Testing conversion detection and calculation:")
    print()
    
    total_expected_value = Decimal('0')
    total_actual_value = Decimal('0')
    
    for etf in problematic_etfs:
        # Test if the ticker is correctly identified for conversion
        should_convert = exporter._is_uk_etf_priced_in_pence(etf['ticker'], etf['api_price_pence'])
        
        if should_convert:
            converted_price = exporter._convert_pence_to_pounds(etf['api_price_pence'])
            market_value = etf['shares'] * converted_price
        else:
            converted_price = etf['api_price_pence']
            market_value = etf['shares'] * converted_price
        
        # Round to 2 decimal places for comparison
        market_value = market_value.quantize(Decimal('0.01'))
        
        print(f"--- {etf['name']} ({etf['ticker']})")
        print(f"   API Price: {etf['api_price_pence']} pence")
        print(f"   Should Convert: {should_convert}")
        print(f"   Converted Price: £{converted_price}")
        print(f"   Expected Price: £{etf['expected_pounds']}")
        print(f"   Shares: {etf['shares']}")
        print(f"   Market Value: £{market_value}")
        print(f"   Expected Value: £{etf['expected_market_value']}")
        
        # Check if conversion is correct
        price_correct = abs(converted_price - etf['expected_pounds']) < Decimal('0.01')
        value_correct = abs(market_value - etf['expected_market_value']) < Decimal('0.10')
        
        if price_correct and value_correct:
            print(f"   CORRECT - Price and value calculations match expected results")
        else:
            print(f"   ERROR - Calculations don't match expected results")
            if not price_correct:
                print(f"      Price mismatch: got £{converted_price}, expected £{etf['expected_pounds']}")
            if not value_correct:
                print(f"      Value mismatch: got £{market_value}, expected £{etf['expected_market_value']}")
        
        total_expected_value += etf['expected_market_value']
        total_actual_value += market_value
        print()
    
    print("=" * 60)
    print("SUMMARY")
    print(f"Total Expected Value (3 positions): £{total_expected_value}")
    print(f"Total Calculated Value: £{total_actual_value}")
    print(f"Difference: £{total_actual_value - total_expected_value}")
    
    if abs(total_actual_value - total_expected_value) < Decimal('1.00'):
        print("SUCCESS: Conversion logic is working correctly!")
        print("The fix should resolve the £1,354.17 portfolio discrepancy.")
    else:
        print("ISSUE: Conversion logic needs adjustment")
        
    print("\nNext Steps:")
    print("1. Test with real API data to confirm API returns prices in pence")
    print("2. If confirmed, the fix is ready for production")
    print("3. Remove debug logging once verified")

if __name__ == "__main__":
    verify_conversion_logic()