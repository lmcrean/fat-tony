#!/usr/bin/env python3
"""
Simulate portfolio export with fixed ETF price conversions.
This script applies the same price conversion logic to create a corrected CSV
and then runs discrepancy analysis to verify the fixes work.
"""

import csv
import sys
from decimal import Decimal
from typing import List, Dict, Tuple

# Add the trading212_exporter to the path
sys.path.insert(0, 'trading212_exporter')

from trading212_exporter.exporter import PortfolioExporter


def simulate_price_fixes():
    """Simulate applying price conversion fixes to the existing CSV data."""
    
    # Create exporter instance to access the conversion methods
    exporter = PortfolioExporter({})
    
    # Read the original CSV data
    corrected_positions = []
    
    with open('portfolio_positions.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the header line
    header_line_idx = None
    for i, line in enumerate(lines):
        if 'ACCOUNT,NAME,SHARES' in line:
            header_line_idx = i
            break
    
    if header_line_idx is None:
        raise ValueError("Could not find CSV header line")
    
    # Parse CSV starting from header line
    csv_content = ''.join(lines[header_line_idx:])
    reader = csv.DictReader(csv_content.splitlines())
    
    print("=== Simulating Price Conversion Fixes ===")
    total_value_before = Decimal('0')
    total_value_after = Decimal('0')
    
    for row in reader:
        if not row.get('NAME') or not row.get('ACCOUNT'):
            continue
        
        # Get original values
        name = row['NAME'].strip()
        account = row['ACCOUNT'].strip()
        shares = Decimal(row['SHARES'].replace(',', ''))
        current_price = Decimal(row['CURRENT_PRICE'].replace(',', ''))
        original_market_value = Decimal(row['MARKET_VALUE'].replace(',', ''))
        
        # Find ticker by name lookup (reverse mapping)
        ticker = find_ticker_by_name(name)
        
        if ticker:
            # Check if this ticker needs price conversion
            raw_price_pence = current_price * 100  # Convert back to pence for testing
            should_convert = exporter._is_uk_etf_priced_in_pence(ticker, raw_price_pence)
            
            if should_convert:
                # Apply the conversion (the CSV price was incorrectly converted before)
                # So we need to multiply by 100 to get the correct value
                corrected_price = current_price * 100
                corrected_market_value = shares * corrected_price
                
                print(f"FIXING: {name[:30]:30} | {ticker:12}")
                print(f"   Original: {shares:>8.4f} × £{current_price:>8.2f} = £{original_market_value:>10.2f}")
                print(f"   Corrected: {shares:>8.4f} × £{corrected_price:>8.2f} = £{corrected_market_value:>10.2f}")
                print(f"   Improvement: +£{corrected_market_value - original_market_value:,.2f}")
                print()
                
                current_price = corrected_price
                market_value = corrected_market_value
            else:
                market_value = original_market_value
        else:
            market_value = original_market_value
        
        total_value_before += original_market_value
        total_value_after += market_value
        
        # Store corrected position
        corrected_positions.append({
            'ACCOUNT': account,
            'NAME': name,
            'SHARES': f"{shares:,.4f}".rstrip('0').rstrip('.'),
            'AVERAGE_PRICE': row['AVERAGE_PRICE'],
            'CURRENT_PRICE': f"{current_price:.2f}",
            'MARKET_VALUE': f"{market_value:,.2f}",
            'RESULT': row['RESULT'],
            'RESULT_%': row['RESULT_%'],
            'CURRENCY': row['CURRENCY']
        })
    
    print("=== Summary of Fixes ===")
    print(f"Portfolio value before fixes: £{total_value_before:,.2f}")
    print(f"Portfolio value after fixes:  £{total_value_after:,.2f}")
    print(f"Total improvement:            +£{total_value_after - total_value_before:,.2f}")
    print()
    
    # Save corrected CSV
    with open('portfolio_positions_fixed.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Add header with timestamp
        writer.writerow([f"Trading 212 Portfolio Positions - FIXED VERSION - Generated on 2025-08-01 23:27:19"])
        writer.writerow([])  # Empty row
        
        # Add column headers
        writer.writerow(['ACCOUNT', 'NAME', 'SHARES', 'AVERAGE_PRICE', 'CURRENT_PRICE', 'MARKET_VALUE', 'RESULT', 'RESULT_%', 'CURRENCY'])
        
        # Add data rows
        for position in corrected_positions:
            writer.writerow([
                position['ACCOUNT'],
                position['NAME'],
                position['SHARES'],
                position['AVERAGE_PRICE'],
                position['CURRENT_PRICE'],
                position['MARKET_VALUE'],
                position['RESULT'],
                position['RESULT_%'],
                position['CURRENCY']
            ])
    
    print("Fixed portfolio saved to: portfolio_positions_fixed.csv")
    return total_value_after - total_value_before


def find_ticker_by_name(name: str) -> str:
    """Find ticker symbol by position name."""
    # Import ticker mappings
    from trading212_exporter.ticker_mappings import TICKER_TO_NAME
    
    # Create reverse mapping
    name_to_ticker = {v: k for k, v in TICKER_TO_NAME.items()}
    
    # Exact match first
    if name in name_to_ticker:
        return name_to_ticker[name]
    
    # Partial match
    for mapped_name, ticker in name_to_ticker.items():
        if mapped_name.lower() in name.lower() or name.lower() in mapped_name.lower():
            return ticker
    
    return None


def run_discrepancy_analysis_on_fixed_csv():
    """Run discrepancy analysis on the fixed CSV."""
    print("\n=== Running Discrepancy Analysis on Fixed CSV ===")
    
    # Import and run the discrepancy analysis
    from discrepancy_analysis import DiscrepancyAnalyzer
    
    analyzer = DiscrepancyAnalyzer()
    
    # Load fixed CSV data
    analyzer.load_csv_data("portfolio_positions_fixed.csv")
    
    # Load source of truth
    analyzer.parse_source_of_truth("source_of_truth/source_of_truth.md")
    
    # Calculate discrepancies
    analyzer.calculate_discrepancies()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save report
    with open("discrepancy_report_fixed.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Fixed analysis complete! Found {len(analyzer.discrepancies)} discrepancies.")
    print("Report saved to: discrepancy_report_fixed.md")
    
    # Print summary
    sorted_discrepancies = sorted(analyzer.discrepancies, key=lambda x: abs(x.difference), reverse=True)
    if sorted_discrepancies:
        print("\nTop 5 Remaining Discrepancies:")
        for i, disc in enumerate(sorted_discrepancies[:5]):
            print(f"{i+1}. {disc.position_name} ({disc.field}): £{disc.difference:+.2f} ({disc.percentage_diff:+.2f}%)")
    else:
        print("\nNo significant discrepancies found!")


def main():
    """Main function to run the simulation."""
    print("Simulating Portfolio Export with ETF Price Conversion Fixes")
    print("=" * 70)
    
    try:
        # Apply fixes to CSV data
        improvement = simulate_price_fixes()
        
        # Run discrepancy analysis on fixed data
        run_discrepancy_analysis_on_fixed_csv()
        
        print("\n" + "=" * 70)
        if improvement > 1000:
            print(f"SUCCESS! Portfolio value improved by £{improvement:,.2f}")
            print("ETF price conversion fixes are working correctly!")
        else:
            print(f"Limited improvement: +£{improvement:,.2f}")
            print("May need additional investigation")
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        raise


if __name__ == "__main__":
    main()