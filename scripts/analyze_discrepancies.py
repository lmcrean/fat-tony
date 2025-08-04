#!/usr/bin/env python3
"""
Updated Discrepancy Analysis Tool
Compares portfolio_positions_FINAL.csv with source_of_truth.gbp.csv
Handles Trading 212's internal ticker format mapping
"""

import csv
from decimal import Decimal
from typing import Dict, List, Tuple
from datetime import datetime


# Ticker mapping from Trading 212 format to standard format
TICKER_MAPPING = {
    # US Stocks
    'NVDA_US_EQ': 'NVDA',
    'PLTR_US_EQ': 'PLTR',
    'AVGO_US_EQ': 'AVGO',
    'ORCL_US_EQ': 'ORCL',
    'SHOP_US_EQ': 'SHOP',
    'MSFT_US_EQ': 'MSFT',
    'V_US_EQ': 'V',
    'SPOT_US_EQ': 'SPOT',
    'FB_US_EQ': 'META',
    'MA_US_EQ': 'MA',
    'NFLX_US_EQ': 'NFLX',
    'AAXN_US_EQ': 'AXON',
    'GOOGL_US_EQ': 'GOOGL',
    'UBER_US_EQ': 'UBER',
    'OAC_US_EQ': 'HIMS',
    'RDDT_US_EQ': 'RDDT',
    'MSTR_US_EQ': 'MSTR',
    'ASML_US_EQ': 'ASML',
    'AMZN_US_EQ': 'AMZN',
    'PGR_US_EQ': 'PGR',
    'ISRG_US_EQ': 'ISRG',
    'FIG_US_EQ': 'FIGMA',
    
    # UK Stocks and ETFs
    'RMVl_EQ': 'RMV.L',
    'SGLNl_EQ': 'SGLN.L',
    'VUAGl_EQ': 'VUSA.L',
    'INTLl_EQ': 'WTAI.L',
    'BLKCa_EQ': 'IBLC.L',
    'RBODl_EQ': 'RBOT.L',
    'SMGBl_EQ': 'SMH',
    'VWRPl_EQ': 'VWRL.L',
    'EXICd_EQ': 'DAXE.L',
    'VGERl_EQ': 'VGEM.L',
    'IINDl_EQ': 'IIND.L',
    'R1GRl_EQ': 'IWF',
    'FXACa_EQ': 'FXACa',  # Keep as is for now
    'IITU_EQ': 'IITU.L',
    'CNX1_EQ': 'CNX1.L',
    
    # Additional mappings
    'IUKDl_EQ': 'IUKD.L',
}


def parse_currency_value(value_str: str) -> Decimal:
    """Parse currency string to Decimal"""
    if not value_str:
        return Decimal('0')
    
    # Remove currency symbols, quotes, and commas
    cleaned = str(value_str).strip().replace('£', '').replace('$', '').replace(',', '').replace('"', '').replace('+', '')
    
    try:
        return Decimal(cleaned)
    except:
        return Decimal('0')


def load_our_positions(csv_path: str) -> Dict[str, Dict]:
    """Load positions from portfolio_positions_FINAL.csv"""
    positions = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            t212_ticker = row['Ticker']
            
            # Map to standard ticker
            standard_ticker = TICKER_MAPPING.get(t212_ticker, t212_ticker)
            
            positions[standard_ticker] = {
                't212_ticker': t212_ticker,
                'name': row['Name'],
                'account': row['Account Type'],
                'quantity': parse_currency_value(row['Quantity of Shares']),
                'avg_price_gbp': parse_currency_value(row['Price Owned (GBP)']),
                'current_price_gbp': parse_currency_value(row['Current Price (GBP)']),
                'market_value_gbp': parse_currency_value(row['Value (GBP)']),
                'change_gbp': parse_currency_value(row['Change (GBP)']),
                'change_pct': parse_currency_value(row['Change %']),
            }
    
    return positions


def load_source_positions(csv_path: str) -> Dict[str, Dict]:
    """Load positions from source_of_truth.gbp.csv"""
    positions = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row['Ticker']
            
            positions[ticker] = {
                'name': row['Name'],
                'account': row['Account Type'],
                'quantity': parse_currency_value(row['Quantity of Shares']),
                'avg_price_gbp': parse_currency_value(row['Price Owned (GBP)']),
                'current_price_gbp': parse_currency_value(row['Current Price (GBP)']),
                'market_value_gbp': parse_currency_value(row['Value (GBP)']),
                'change_gbp': parse_currency_value(row['Change (GBP)']),
                'change_pct': parse_currency_value(row['Change %']),
            }
    
    return positions


def compare_positions(our_positions: Dict, source_positions: Dict) -> Tuple[List, List, List]:
    """Compare positions and return matches, price discrepancies, and quantity discrepancies"""
    matches = []
    price_discrepancies = []
    quantity_discrepancies = []
    
    # Find common positions
    common_tickers = set(our_positions.keys()) & set(source_positions.keys())
    
    for ticker in sorted(common_tickers):
        our = our_positions[ticker]
        source = source_positions[ticker]
        
        matches.append({
            'ticker': ticker,
            'name': our['name'],
            'our_quantity': our['quantity'],
            'source_quantity': source['quantity'],
            'our_price': our['current_price_gbp'],
            'source_price': source['current_price_gbp'],
        })
        
        # Check quantity match
        if abs(our['quantity'] - source['quantity']) > Decimal('0.001'):
            quantity_discrepancies.append({
                'ticker': ticker,
                'name': our['name'],
                'our_quantity': our['quantity'],
                'source_quantity': source['quantity'],
                'difference': our['quantity'] - source['quantity'],
            })
        
        # Check price discrepancy (more than 1% difference is significant)
        if source['current_price_gbp'] > 0:
            price_diff_pct = ((our['current_price_gbp'] - source['current_price_gbp']) / source['current_price_gbp']) * 100
            if abs(price_diff_pct) > 1:
                price_discrepancies.append({
                    'ticker': ticker,
                    'name': our['name'],
                    'our_price': our['current_price_gbp'],
                    'source_price': source['current_price_gbp'],
                    'difference': our['current_price_gbp'] - source['current_price_gbp'],
                    'pct_diff': price_diff_pct,
                })
    
    return matches, price_discrepancies, quantity_discrepancies


def generate_report(our_positions: Dict, source_positions: Dict, matches: List, 
                   price_discrepancies: List, quantity_discrepancies: List) -> str:
    """Generate markdown report"""
    report = []
    report.append("# Portfolio Discrepancy Report")
    report.append("")
    report.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    report.append("")
    
    # Summary
    report.append("## Summary")
    report.append("")
    report.append(f"- **Source of Truth Positions**: {len(source_positions)}")
    report.append(f"- **Our Positions**: {len(our_positions)}")
    report.append(f"- **Common Positions**: {len(matches)}")
    report.append(f"- **Missing Positions**: {len(source_positions) - len(matches)}")
    report.append(f"- **Price Discrepancies**: {len(price_discrepancies)}")
    report.append(f"- **Quantity Discrepancies**: {len(quantity_discrepancies)}")
    report.append("")
    
    # Missing positions
    only_in_source = set(source_positions.keys()) - set(our_positions.keys())
    only_in_ours = set(our_positions.keys()) - set(source_positions.keys())
    
    if only_in_source:
        report.append("## Positions Missing in Our Data")
        report.append("")
        for ticker in sorted(only_in_source):
            pos = source_positions[ticker]
            report.append(f"- {ticker} ({pos['name']})")
        report.append("")
    
    if only_in_ours:
        report.append("## Extra Positions in Our Data")
        report.append("")
        for ticker in sorted(only_in_ours):
            pos = our_positions[ticker]
            report.append(f"- {ticker} ({pos['name']}) [T212: {pos['t212_ticker']}]")
        report.append("")
    
    # Price discrepancies
    if price_discrepancies:
        report.append("## Price Discrepancies")
        report.append("")
        report.append("| Ticker | Name | Source Price (GBP) | Our Price (GBP) | Difference | % Diff |")
        report.append("|--------|------|-------------------|-----------------|------------|--------|")
        
        for disc in sorted(price_discrepancies, key=lambda x: abs(x['pct_diff']), reverse=True):
            report.append(f"| {disc['ticker']} | {disc['name'][:30]} | {disc['source_price']:.2f} | "
                         f"{disc['our_price']:.2f} | {disc['difference']:+.2f} | {disc['pct_diff']:+.2f}% |")
        report.append("")
    
    # Quantity discrepancies
    if quantity_discrepancies:
        report.append("## Quantity Discrepancies")
        report.append("")
        report.append("| Ticker | Name | Source Quantity | Our Quantity | Difference |")
        report.append("|--------|------|-----------------|--------------|------------|")
        
        for disc in quantity_discrepancies:
            report.append(f"| {disc['ticker']} | {disc['name'][:30]} | {disc['source_quantity']:.4f} | "
                         f"{disc['our_quantity']:.4f} | {disc['difference']:+.4f} |")
        report.append("")
    
    # Portfolio value comparison
    our_total = sum(pos['market_value_gbp'] for pos in our_positions.values())
    source_total = sum(pos['market_value_gbp'] for pos in source_positions.values())
    
    report.append("## Portfolio Value Comparison")
    report.append("")
    report.append(f"- **Source of Truth Total**: £{source_total:,.2f}")
    report.append(f"- **Our Total**: £{our_total:,.2f}")
    report.append(f"- **Difference**: £{our_total - source_total:+,.2f}")
    report.append(f"- **Percentage Difference**: {((our_total - source_total) / source_total * 100):+.2f}%")
    report.append("")
    
    report.append("## Notes")
    report.append("")
    report.append("- Price differences are expected due to market movements since the source of truth was captured")
    report.append("- Discrepancies > 1% are highlighted as they may indicate data issues beyond normal market movement")
    report.append("- Ticker mapping: Trading 212 internal format (e.g., NVDA_US_EQ) is mapped to standard format (e.g., NVDA)")
    
    return "\n".join(report)


def main():
    """Main function"""
    # Load data
    print("Loading portfolio data...")
    our_positions = load_our_positions("output/portfolio_positions_FINAL.csv")
    source_positions = load_source_positions("source_of_truth/source_of_truth.gbp.csv")
    
    # Compare
    print("Comparing positions...")
    matches, price_discrepancies, quantity_discrepancies = compare_positions(our_positions, source_positions)
    
    # Generate report
    print("Generating report...")
    report = generate_report(our_positions, source_positions, matches, 
                           price_discrepancies, quantity_discrepancies)
    
    # Save report
    with open("output/discrepancy_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\nAnalysis complete!")
    print(f"- Found {len(matches)} matching positions")
    print(f"- {len(price_discrepancies)} positions with significant price differences")
    print(f"- {len(quantity_discrepancies)} positions with quantity mismatches")
    print(f"\nReport saved to: output/discrepancy_report.md")


if __name__ == "__main__":
    main()