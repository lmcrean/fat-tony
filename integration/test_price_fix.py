#!/usr/bin/env python3
"""
Test the price conversion fix on problematic positions.
"""

import os
from decimal import Decimal
from dotenv import load_dotenv
from trading212_exporter.client import Trading212Client
from trading212_exporter.exporter import PortfolioExporter

load_dotenv()

def test_price_fix():
    """Test the price conversion fix."""
    print("=== TESTING PRICE CONVERSION FIX ===\n")
    
    api_key = os.getenv("API_KEY_INVEST_ACCOUNT")
    if not api_key:
        print("Error: API_KEY_INVEST_ACCOUNT not found")
        return
    
    # Create just the INVEST account client to test
    clients = {
        'Invest Account': Trading212Client(api_key, account_name='Invest Account')
    }
    
    # Create exporter with new conversion logic
    exporter = PortfolioExporter(clients)
    
    # Test the conversion function directly first
    print("Testing conversion detection logic:")
    test_cases = [
        ("IITU_EQ", Decimal("2827.0")),      # Should convert
        ("INTLl_EQ", Decimal("5557.5")),     # Should convert  
        ("SGLNl_EQ", Decimal("4910")),       # Should convert
        ("CNX1_EQ", Decimal("98520.0")),     # Should convert
        ("RMVl_EQ", Decimal("812.2")),       # Should NOT convert (< 1000)
        ("GOOGL_US_EQ", Decimal("188.73")),  # Should NOT convert (US stock)
        ("VUAGl_EQ", Decimal("8998.0")),     # Should convert (in pence)
        ("VGERl_EQ", Decimal("2943.0")),     # Should convert (in pence)
        ("SMGBl_EQ", Decimal("3553.0")),     # Should convert (in pence)
    ]
    
    for ticker, price in test_cases:
        should_convert = exporter._is_uk_etf_priced_in_pence(ticker, price)
        if should_convert:
            converted = exporter._convert_pence_to_pounds(price)
            print(f"  {ticker}: {price} -> {converted} (CONVERTED)")
        else:
            print(f"  {ticker}: {price} (NO CONVERSION)")
    
    print(f"\n{'='*60}")
    print("Testing with real API data (first 10 positions)...")
    print(f"{'='*60}")
    
    # Get raw data from invest account
    invest_client = clients['Invest Account']
    raw_portfolio = invest_client.get_portfolio()
    
    # Test first 10 positions
    for i, position_data in enumerate(raw_portfolio[:10]):
        ticker = position_data.get('ticker', 'Unknown')
        raw_current = Decimal(str(position_data.get('currentPrice', 0)))
        raw_avg = Decimal(str(position_data.get('averagePrice', 0)))
        
        # Test conversion logic
        should_convert = exporter._is_uk_etf_priced_in_pence(ticker, raw_current)
        
        if should_convert:
            converted_current = exporter._convert_pence_to_pounds(raw_current)
            converted_avg = exporter._convert_pence_to_pounds(raw_avg)
            print(f"\n{ticker}:")
            print(f"  RAW: avg={raw_avg}, current={raw_current}")
            print(f"  CONVERTED: avg={converted_avg}, current={converted_current}")
        else:
            print(f"\n{ticker}: No conversion needed (avg={raw_avg}, current={raw_current})")

if __name__ == "__main__":
    test_price_fix()