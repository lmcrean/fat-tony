#!/usr/bin/env python3
"""
Debug specific ETF pricing to see if it's account or ticker specific.
"""

import os
from dotenv import load_dotenv
from trading212_exporter.client import Trading212Client

load_dotenv()

def debug_specific_etf():
    """Check if same ETFs have different prices in different accounts."""
    print("=== ETF PRICE COMPARISON BETWEEN ACCOUNTS ===\n")
    
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
    
    # Get all tickers from both accounts
    all_positions = {}
    
    for account_type, account_info in accounts.items():
        api_key = account_info["api_key"]
        if not api_key:
            continue
            
        client = Trading212Client(api_key, account_info["display_name"])
        portfolio = client.get_portfolio()
        
        print(f"\n{account_type} Account positions:")
        positions_by_ticker = {}
        for pos in portfolio:
            ticker = pos.get('ticker')
            price = pos.get('currentPrice', 0)
            positions_by_ticker[ticker] = price
            print(f"  {ticker}: {price}")
        
        all_positions[account_type] = positions_by_ticker
    
    # Find common tickers
    isa_tickers = set(all_positions.get('ISA', {}).keys())
    invest_tickers = set(all_positions.get('INVEST', {}).keys())
    common_tickers = isa_tickers & invest_tickers
    
    print(f"\n{'='*60}")
    print(f"COMMON TICKERS PRICE COMPARISON")
    print(f"{'='*60}")
    print(f"Found {len(common_tickers)} common tickers: {common_tickers}")
    
    for ticker in common_tickers:
        isa_price = all_positions['ISA'][ticker]
        invest_price = all_positions['INVEST'][ticker]
        ratio = invest_price / isa_price if isa_price != 0 else 0
        
        print(f"\n{ticker}:")
        print(f"  ISA price: {isa_price}")
        print(f"  INVEST price: {invest_price}")
        print(f"  Ratio (INVEST/ISA): {ratio:.2f}")
        
        if abs(ratio - 100) < 1:
            print(f"  *** 100x INFLATION in INVEST account!")
        elif abs(ratio - 1) < 0.01:
            print(f"  OK: Prices match")
        else:
            print(f"  WARNING: Unexpected ratio")
    
    # Check some INVEST-only ETFs that showed problems
    print(f"\n{'='*60}")
    print(f"INVEST-ONLY PROBLEMATIC ETFS")
    print(f"{'='*60}")
    
    problematic_etfs = {
        "IITU_EQ": "iShares S&P 500 Information Technology Sector",
        "INTLl_EQ": "WisdomTree Artificial Intelligence", 
        "SGLNl_EQ": "iShares Physical Gold",
        "CNX1_EQ": "iShares NASDAQ 100",
        "RMVl_EQ": "Rightmove"
    }
    
    invest_positions = all_positions.get('INVEST', {})
    for ticker, name in problematic_etfs.items():
        if ticker in invest_positions:
            price = invest_positions[ticker]
            print(f"{ticker} ({name}): {price}")
            
            # Check if this looks like pence
            if price >= 1000:
                print(f"  *** SUSPICIOUS: Price {price} >= 1000 (likely pence, should be £{price/100:.2f})")
            else:
                print(f"  OK: NORMAL: Price {price} < 1000")

if __name__ == "__main__":
    debug_specific_etf()