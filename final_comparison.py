#!/usr/bin/env python3
"""
Final comparison between the fixed CSV and source of truth.
"""

import csv
import sys
import os
from decimal import Decimal

def compare_files():
    """Compare portfolio_positions_FIXED.csv with source_of_truth.gbp.csv"""
    
    # Ticker mapping between source format and Trading 212 API format
    ticker_mapping = {
        'PLTR': 'PLTR_US_EQ',
        'NVDA': 'NVDA_US_EQ', 
        'RMV.L': 'RMVl_EQ',
        'SGLN.L': 'SGLNl_EQ',
        'IITU.L': 'IITU_EQ',
        'WTAI.L': 'INTLl_EQ',
        'CNX1.L': 'CNX1_EQ',
        'VUSA.L': 'VUAGl_EQ',
        'IUKD.L': 'FXACa_EQ',
        'DAXE.L': 'EXICd_EQ',
        'IIND.L': 'IINDl_EQ',
    }
    
    # Load source of truth
    source_data = {}
    try:
        with open('source_of_truth/source_of_truth.gbp.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Ticker', '')
                if ticker:
                    source_data[ticker] = row
    except FileNotFoundError:
        print("Source of truth file not found!")
        return

    # Load our fixed data
    our_data = {}
    try:
        with open('output/portfolio_positions_FIXED.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Ticker', '')
                if ticker:
                    our_data[ticker] = row
    except FileNotFoundError:
        print("Fixed CSV file not found!")
        return

    print("=== FINAL COMPARISON RESULTS ===")
    print(f"Source positions: {len(source_data)}")
    print(f"Our positions: {len(our_data)}")
    print()

    # Find common tickers using mapping
    mappable_matches = 0
    perfect_matches = 0
    close_matches = 0
    significant_differences = 0
    
    print("\n=== DETAILED COMPARISON ===")
    
    for source_ticker, our_ticker in ticker_mapping.items():
        if source_ticker in source_data and our_ticker in our_data:
            mappable_matches += 1
            source_row = source_data[source_ticker]
            our_row = our_data[our_ticker]
        
        # Compare current prices (GBP)
        try:
            source_price = float(source_row.get('Current Price (GBP)', '0'))
            our_price = float(our_row.get('Current Price (GBP)', '0'))
            
            diff = abs(source_price - our_price)
            diff_percent = (diff / source_price * 100) if source_price > 0 else 0
            
            print(f"{ticker:12} | Source: {source_price:8.2f} | Ours: {our_price:8.2f} | Diff: {diff:6.2f} ({diff_percent:5.1f}%)")
            
            if diff < 0.01:
                perfect_matches += 1
            elif diff_percent < 1.0:
                close_matches += 1
            else:
                significant_differences += 1
                
        except (ValueError, TypeError):
            print(f"{ticker:12} | ERROR: Could not compare prices")
    
    print(f"\n=== SUMMARY ===")
    print(f"Perfect matches (< 1p diff):  {perfect_matches}")
    print(f"Close matches (< 1% diff):    {close_matches}")
    print(f"Significant differences:      {significant_differences}")
    print(f"Total accuracy: {(perfect_matches + close_matches) / len(common_tickers) * 100:.1f}%")

if __name__ == "__main__":
    compare_files()