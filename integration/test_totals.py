#!/usr/bin/env python3
"""
Test the fixed export totals by processing the key problematic positions.
"""

import os
from decimal import Decimal
from dotenv import load_dotenv
from trading212_exporter.client import Trading212Client
from trading212_exporter.exporter import PortfolioExporter
from trading212_exporter.models import Position

load_dotenv()

def test_totals():
    """Test the export totals with fixed conversion."""
    print("=== TESTING EXPORT TOTALS WITH PRICE FIX ===\n")
    
    api_key = os.getenv("API_KEY_INVEST_ACCOUNT")
    if not api_key:
        print("Error: API_KEY_INVEST_ACCOUNT not found")
        return
    
    # Create INVEST account client
    clients = {
        'Invest Account': Trading212Client(api_key, account_name='Invest Account')
    }
    
    # Create exporter with conversion logic
    exporter = PortfolioExporter(clients)
    
    # Get raw data
    invest_client = clients['Invest Account']
    raw_portfolio = invest_client.get_portfolio()
    
    print("Processing positions with conversion logic...")
    
    # Focus on the 4 problematic ETFs plus a few others for comparison
    test_tickers = ['IITU_EQ', 'INTLl_EQ', 'SGLNl_EQ', 'CNX1_EQ', 'VUAGl_EQ', 'NVDA_US_EQ']
    
    total_market_value_old = Decimal('0')
    total_market_value_new = Decimal('0')
    
    print(f"{'TICKER':<12} | {'RAW PRICE':<10} | {'FIXED PRICE':<11} | {'SHARES':<8} | {'OLD VALUE':<12} | {'NEW VALUE':<12}")
    print("-" * 85)
    
    for position_data in raw_portfolio:
        ticker = position_data.get('ticker', 'Unknown')
        if ticker not in test_tickers:
            continue
            
        quantity = Decimal(str(position_data.get('quantity', 0)))
        raw_current = Decimal(str(position_data.get('currentPrice', 0)))
        
        # Apply conversion if needed
        if exporter._is_uk_etf_priced_in_pence(ticker, raw_current):
            fixed_current = exporter._convert_pence_to_pounds(raw_current)
        else:
            fixed_current = raw_current
        
        # Calculate market values
        old_market_value = quantity * raw_current
        new_market_value = quantity * fixed_current
        
        total_market_value_old += old_market_value
        total_market_value_new += new_market_value
        
        print(f"{ticker:<12} | {raw_current:<10} | {fixed_current:<11} | {quantity:<8.2f} | {old_market_value:<12,.0f} | {new_market_value:<12,.0f}")
    
    print("-" * 85)
    print(f"{'TOTALS':<12} | {'':<10} | {'':<11} | {'':<8} | {total_market_value_old:<12,.0f} | {total_market_value_new:<12,.0f}")
    
    # Calculate the correction factor
    correction_factor = float(total_market_value_old / total_market_value_new) if total_market_value_new > 0 else 0
    
    print(f"\nCORRECTION SUMMARY:")
    print(f"Old total (inflated): £{total_market_value_old:,.2f}")
    print(f"New total (corrected): £{total_market_value_new:,.2f}")
    print(f"Reduction factor: {correction_factor:.2f}x")
    
    # Compare with source of truth expectations
    expected_total = 8450  # From source of truth: ~£8,450 for INVEST account
    print(f"\nSOURCE OF TRUTH COMPARISON:")
    print(f"Expected total: ~£{expected_total:,}")
    print(f"Corrected total: £{total_market_value_new:,.2f}")
    print(f"Difference: £{abs(float(total_market_value_new) - expected_total):,.2f}")
    
    if abs(float(total_market_value_new) - expected_total) < 1000:
        print("✅ TOTALS NOW MATCH SOURCE OF TRUTH!")
    else:
        print("❌ Still some discrepancy with source of truth")

if __name__ == "__main__":
    test_totals()