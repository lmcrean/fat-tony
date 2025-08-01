#!/usr/bin/env python3
"""
Debug script to identify calculation discrepancies by comparing raw API data 
with the processed results from our exporter.
"""

import os
from decimal import Decimal
from typing import Dict, List

from dotenv import load_dotenv
from trading212_exporter.client import Trading212Client
from trading212_exporter.exporter import PortfolioExporter
from trading212_exporter.ticker_mappings import get_display_name

# Load environment variables
load_dotenv()

def debug_calculations():
    """Compare raw API data with processed exporter results."""
    print("=== DEBUGGING CALCULATION DISCREPANCIES ===\n")
    
    # Get API keys
    api_key_invest = os.getenv("API_KEY_INVEST_ACCOUNT")
    if not api_key_invest:
        print("Error: API_KEY_INVEST_ACCOUNT not found")
        return
    
    # Create client and exporter
    clients = {
        'Invest Account': Trading212Client(api_key_invest, account_name='Invest Account')
    }
    exporter = PortfolioExporter(clients)
    
    print("Fetching raw API data...")
    invest_client = clients['Invest Account']
    raw_portfolio = invest_client.get_portfolio()
    
    print(f"Found {len(raw_portfolio)} positions in raw API data")
    
    # Focus on the most problematic positions
    focus_tickers = [
        "IUIT_US_EQ",  # iShares S&P 500 IT - shows 100x inflation
        "CNX1_EQ",     # iShares NASDAQ 100
        "SGLNl_EQ",    # iShares Physical Gold
        "RMVl_EQ",     # Rightmove
        "INTLl_EQ"     # WisdomTree AI
    ]
    
    print("\n" + "="*80)
    print("RAW API DATA ANALYSIS")
    print("="*80)
    
    # Analyze raw API data for key positions
    for position in raw_portfolio:
        ticker = position.get('ticker', 'Unknown')
        if ticker in focus_tickers:
            quantity = Decimal(str(position.get('quantity', 0)))
            avg_price = Decimal(str(position.get('averagePrice', 0)))
            current_price = Decimal(str(position.get('currentPrice', 0)))
            api_ppl = position.get('ppl', 0)  # API's profit/loss calculation
            
            # Calculate our own values
            market_value = quantity * current_price
            cost_basis = quantity * avg_price
            our_ppl = market_value - cost_basis
            
            display_name = get_display_name(ticker)
            
            print(f"\nTICKER: {ticker} ({display_name})")
            print(f"  Raw API Data:")
            print(f"    quantity: {quantity}")
            print(f"    averagePrice: {avg_price}")
            print(f"    currentPrice: {current_price}")
            print(f"    API ppl: {api_ppl}")
            print(f"  Our Calculations:")
            print(f"    market_value: {market_value}")
            print(f"    cost_basis: {cost_basis}")
            print(f"    our_ppl: {our_ppl}")
            print(f"  Comparison:")
            print(f"    Our PnL vs API PnL: {our_ppl} vs {api_ppl}")
            print(f"    Match: {abs(float(our_ppl) - api_ppl) < 1.0}")
    
    print("\n" + "="*80)
    print("EXPORTER PROCESSED DATA ANALYSIS")
    print("="*80)
    
    # Now fetch processed data through exporter
    print("Processing data through exporter...")
    exporter.fetch_data()
    
    print(f"Exporter found {len(exporter.positions)} processed positions")
    
    # Compare exporter results
    for position in exporter.positions:
        if position.ticker in focus_tickers:
            print(f"\nEXPORTER RESULT FOR {position.ticker}:")
            print(f"  name: {position.name}")
            print(f"  shares: {position.shares}")
            print(f"  average_price: {position.average_price}")
            print(f"  current_price: {position.current_price}")
            print(f"  market_value: {position.market_value}")
            print(f"  cost_basis: {position.cost_basis}")
            print(f"  profit_loss: {position.profit_loss}")
            print(f"  currency: {position.currency}")
            
            # Find matching raw API data
            raw_match = None
            for raw_pos in raw_portfolio:
                if raw_pos.get('ticker') == position.ticker:
                    raw_match = raw_pos
                    break
            
            if raw_match:
                print(f"  COMPARISON WITH RAW API:")
                print(f"    Current price: EXPORTER={position.current_price} vs API={raw_match.get('currentPrice')}")
                print(f"    Market value: EXPORTER={position.market_value} vs API_CALC={Decimal(str(raw_match.get('quantity', 0))) * Decimal(str(raw_match.get('currentPrice', 0)))}")
                
                # Check for 100x factor
                api_current = Decimal(str(raw_match.get('currentPrice', 0)))
                ratio = position.current_price / api_current if api_current != 0 else 0
                print(f"    Price ratio (exporter/api): {ratio}")
                if abs(float(ratio) - 100) < 1:
                    print(f"    🚨 FOUND 100x INFLATION!")
                elif abs(float(ratio) - 1) < 0.01:
                    print(f"    ✅ Prices match")
                else:
                    print(f"    ⚠️  Unexpected ratio: {ratio}")

    print("\n" + "="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    
    # Compare totals
    if 'Invest Account' in exporter.account_summaries:
        summary = exporter.account_summaries['Invest Account']
        print(f"EXPORTER SUMMARY:")
        print(f"  Total Portfolio Value: {summary.invested}")
        print(f"  Total Profit/Loss: {summary.result}")
        print(f"  Free Funds: {summary.free_funds}")
    
    # Get raw cash data
    try:
        cash_data = invest_client.get_account_cash()
        print(f"RAW API CASH DATA:")
        print(f"  invested: {cash_data.get('invested', 'N/A')}")
        print(f"  ppl: {cash_data.get('ppl', 'N/A')}")
        print(f"  free: {cash_data.get('free', 'N/A')}")
        
        if 'Invest Account' in exporter.account_summaries:
            api_invested = cash_data.get('invested', 0)
            exporter_invested = float(summary.invested)
            ratio = exporter_invested / api_invested if api_invested != 0 else 0
            print(f"TOTAL INVESTMENT RATIO (exporter/api): {ratio}")
            if abs(ratio - 100) < 1:
                print("🚨 TOTAL SHOWS 100x INFLATION!")
            elif abs(ratio - 1) < 0.1:
                print("✅ Totals roughly match")
            else:
                print(f"⚠️  Unexpected total ratio: {ratio}")
                
    except Exception as e:
        print(f"Could not get cash data: {e}")

if __name__ == "__main__":
    debug_calculations()