#!/usr/bin/env python3
"""
Debug script to examine currency codes and price units from API responses.
"""

import os
import json
from dotenv import load_dotenv
from trading212_exporter.client import Trading212Client

# Load environment variables
load_dotenv()

def debug_currency():
    """Debug currency codes and price units."""
    print("=== CURRENCY AND PRICE UNIT DEBUGGING ===\n")
    
    accounts = {
        "ISA": {
            "api_key": os.getenv("API_KEY_STOCKS_ISA"),
            "display_name": "Stocks & Shares ISA"
        },
        "INVEST": {
            "api_key": os.getenv("API_KEY_INVEST_ACCOUNT"), 
            "display_name": "Invest Account"
        }
    }
    
    for account_type, account_info in accounts.items():
        api_key = account_info["api_key"]
        display_name = account_info["display_name"]
        
        if not api_key:
            continue
            
        print(f"\n{'='*50}")
        print(f"{account_type} ACCOUNT ({display_name})")
        print(f"{'='*50}")
        
        client = Trading212Client(api_key, display_name)
        
        # Get account metadata
        try:
            metadata = client.get_account_metadata()
            print(f"Account metadata: {json.dumps(metadata, indent=2)}")
        except Exception as e:
            print(f"Could not get metadata: {e}")
        
        # Get sample positions to check currency codes
        try:
            portfolio = client.get_portfolio()
            print(f"\nFound {len(portfolio)} positions")
            
            # Focus on ETFs that might have GBX vs GBP issues
            etf_positions = [p for p in portfolio if any(x in p.get('ticker', '') for x in ['_EQ', 'l_EQ'])]
            us_positions = [p for p in portfolio if 'US_EQ' in p.get('ticker', '')]
            
            print(f"ETF/UK positions: {len(etf_positions)}")
            print(f"US positions: {len(us_positions)}")
            
            # Show currency info for a few sample positions
            sample_positions = portfolio[:5]  # First 5 positions
            for pos in sample_positions:
                ticker = pos.get('ticker', 'Unknown')
                currency = pos.get('currencyCode', 'Not specified')
                current_price = pos.get('currentPrice', 0)
                avg_price = pos.get('averagePrice', 0)
                
                print(f"\n  {ticker}:")
                print(f"    currencyCode: {currency}")
                print(f"    currentPrice: {current_price}")
                print(f"    averagePrice: {avg_price}")
                
                # Check if this looks like pence (high numbers for UK stocks)
                if currency == 'GBP' and current_price > 1000:
                    print(f"    🚨 SUSPICIOUS: GBP price {current_price} > 1000 (might be pence)")
                elif currency == 'GBP' and current_price < 100:
                    print(f"    ✅ NORMAL: GBP price {current_price} < 100")
                    
        except Exception as e:
            print(f"Could not get portfolio: {e}")

if __name__ == "__main__":
    debug_currency()