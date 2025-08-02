#!/usr/bin/env python3
"""
Diagnostic script to test Trading 212 API endpoints individually.
This helps identify which endpoints work and which need fixes.
"""

import os
from dotenv import load_dotenv
from trading212_exporter import Trading212Client

def test_endpoints():
    """Test each API endpoint individually."""
    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    if not api_key:
        print("ERROR: No API_KEY found in .env file")
        return
    
    client = Trading212Client(api_key)
    print("API Key loaded successfully")
    print("=" * 50)
    
    # Test each endpoint
    endpoints = [
        ("Portfolio Positions", client.get_portfolio),
        ("Account Cash", client.get_account_cash),
        ("Account Metadata", client.get_account_metadata),
    ]
    
    results = {}
    
    for name, method in endpoints:
        print(f"\nTesting {name}...")
        try:
            result = method()
            print(f"SUCCESS: {name}")
            print(f"   Response type: {type(result)}")
            if isinstance(result, dict):
                print(f"   Keys: {list(result.keys())[:5]}...")  # Show first 5 keys
            elif isinstance(result, list):
                print(f"   Length: {len(result)}")
                if result and isinstance(result[0], dict):
                    print(f"   First item keys: {list(result[0].keys())[:5]}...")
            results[name] = True
        except Exception as e:
            print(f"FAILED: {name}")
            print(f"   Error: {e}")
            results[name] = False
    
    # Test individual position details if portfolio works
    if results.get("Portfolio Positions"):
        print(f"\nTesting Individual Position Details...")
        try:
            portfolio = client.get_portfolio()
            if portfolio:
                ticker = portfolio[0]['ticker']
                print(f"   Testing with ticker: {ticker}")
                details = client.get_position_details(ticker)
                print(f"SUCCESS: Position Details")
                print(f"   Keys: {list(details.keys())[:5]}...")
            else:
                print("   No positions to test")
        except Exception as e:
            print(f"FAILED: Position Details")
            print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    for name, success in results.items():
        status = "WORKING" if success else "BROKEN"
        print(f"   {name}: {status}")

if __name__ == "__main__":
    test_endpoints()