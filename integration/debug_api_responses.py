#!/usr/bin/env python3
"""
Debug script to examine raw API responses and identify price unit discrepancies.
This will help us understand if the API is returning prices in pence vs pounds.
"""

import os
import json
from decimal import Decimal
from typing import Dict, List

from dotenv import load_dotenv
from trading212_exporter.client import Trading212Client

# Load environment variables
load_dotenv()

def debug_api_responses():
    """Debug API responses to identify price unit issues."""
    
    # Get API keys for different account types - focus on INVEST to debug the big issue
    accounts = {
        "INVEST": {
            "api_key": os.getenv("API_KEY_INVEST_ACCOUNT"), 
            "display_name": "Invest Account"
        }
    }
    
    # Check that we have at least one API key
    if not any(account["api_key"] for account in accounts.values()):
        print("Error: No API keys found in environment variables")
        print("Expected: API_KEY_STOCKS_ISA and/or API_KEY_INVEST_ACCOUNT")
        return
    
    print("=== DEBUGGING TRADING 212 API RESPONSES ===\n")
    
    for account_type, account_info in accounts.items():
        api_key = account_info["api_key"]
        display_name = account_info["display_name"]
        
        if not api_key:
            print(f"Skipping {account_type} - no API key found")
            continue
            
        print(f"\n{'='*50}")
        print(f"DEBUGGING {account_type} ACCOUNT ({display_name})")
        print(f"{'='*50}")
        
        try:
            # Create client for this account type
            client = Trading212Client(api_key, display_name)
            
            # Get raw portfolio data
            print("\n--- RAW PORTFOLIO DATA ---")
            portfolio_data = client.get_portfolio()
            print(f"Number of positions: {len(portfolio_data)}")
            
            # Focus on positions that showed huge discrepancies
            focus_tickers = [
                "IUIT_US_EQ",  # iShares S&P 500 IT
                "WTAI_LN",     # WisdomTree AI
                "SGLN_LN",     # iShares Physical Gold
                "INQQ_LN",     # iShares NASDAQ 100
                "RMV_LN"       # Rightmove
            ]
            
            for position in portfolio_data:
                ticker = position.get('ticker', 'Unknown')
                
                # Show detailed info for problematic positions or all if small portfolio
                if ticker in focus_tickers or len(portfolio_data) <= 15:
                    print(f"\n  TICKER: {ticker}")
                    print(f"  Raw API response: {json.dumps(position, indent=4)}")
                    
                    # Skip position details to avoid rate limits - we have the key data already
                    
                    # Calculate values manually to check math
                    quantity = Decimal(str(position.get('quantity', 0)))
                    avg_price = Decimal(str(position.get('averagePrice', 0)))
                    current_price = Decimal(str(position.get('currentPrice', 0)))
                    
                    market_value = quantity * current_price
                    cost_basis = quantity * avg_price
                    profit_loss = market_value - cost_basis
                    
                    print(f"  CALCULATED VALUES:")
                    print(f"    Quantity: {quantity}")
                    print(f"    Average Price: {avg_price}")
                    print(f"    Current Price: {current_price}")
                    print(f"    Market Value: {market_value}")
                    print(f"    Cost Basis: {cost_basis}")
                    print(f"    Profit/Loss: {profit_loss}")
                    
                    # Check if this matches source of truth
                    print(f"  SOURCE OF TRUTH CHECK:")
                    if ticker == "IUIT_US_EQ":
                        print(f"    Expected Market Value: ~£1,172.92")
                        print(f"    Calculated Market Value: £{market_value}")
                        print(f"    Ratio: {float(market_value) / 1172.92:.2f}x")
                    elif ticker == "WTAI_LN":
                        print(f"    Expected Market Value: ~£235.64") 
                        print(f"    Calculated Market Value: £{market_value}")
                        print(f"    Ratio: {float(market_value) / 235.64:.2f}x")
                    
                    print("-" * 40)
            
            # Get account cash data
            print(f"\n--- ACCOUNT CASH DATA ---")
            try:
                cash_data = client.get_account_cash()
                print(f"Cash data: {json.dumps(cash_data, indent=2)}")
            except Exception as e:
                print(f"Could not get cash data: {e}")
            
            # Get account metadata
            print(f"\n--- ACCOUNT METADATA ---")
            try:
                metadata = client.get_account_metadata()
                print(f"Metadata: {json.dumps(metadata, indent=2)}")
            except Exception as e:
                print(f"Could not get metadata: {e}")
                
        except Exception as e:
            print(f"Error processing {account_type} account: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_api_responses()