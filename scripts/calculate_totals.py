import csv
from pathlib import Path


def calculate_totals(csv_path):
    """Read source_of_truth.csv and calculate totals by account type."""
    totals = {
        'Trading': {'value': 0.0, 'change': 0.0},
        'ISA': {'value': 0.0, 'change': 0.0},
    }
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            account_type = row['Account Type']
            if account_type in totals:
                try:
                    value = float(row['Value (GBP)']) if row['Value (GBP)'] else 0.0
                    change = float(row['Change (GBP)']) if row['Change (GBP)'] else 0.0
                    
                    totals[account_type]['value'] += value
                    totals[account_type]['change'] += change
                except ValueError as e:
                    print(f"Error parsing values for {row['Name']}: {e}")
    
    # Calculate percentages
    for account_type in totals:
        value = totals[account_type]['value']
        change = totals[account_type]['change']
        
        # Calculate change percentage: (change / initial_value) * 100
        # initial_value = current_value - change
        initial_value = value - change
        if initial_value > 0:
            totals[account_type]['change_pct'] = (change / initial_value) * 100
        else:
            totals[account_type]['change_pct'] = 0.0
    
    # Calculate grand total
    grand_total = {
        'value': totals['Trading']['value'] + totals['ISA']['value'],
        'change': totals['Trading']['change'] + totals['ISA']['change'],
    }
    
    # Calculate grand total percentage
    grand_initial = grand_total['value'] - grand_total['change']
    if grand_initial > 0:
        grand_total['change_pct'] = (grand_total['change'] / grand_initial) * 100
    else:
        grand_total['change_pct'] = 0.0
    
    return totals, grand_total


def write_totals_csv(totals, grand_total, output_path, cash_gbp=7128.00):
    """Write the calculated totals to a CSV file in the exact format."""
    
    # Calculate cash/portfolio percentages
    total_with_cash = grand_total['value'] + cash_gbp
    cash_pct = (cash_gbp / total_with_cash * 100)
    portfolio_pct = (grand_total['value'] / total_with_cash * 100)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Account Type', 'Value GBP', 'Change GBP', 'Change %'])
        
        # Write Trading Account totals
        writer.writerow([
            'Trading Acc value GBP',
            f"{totals['Trading']['value']:.2f}",
            f"{totals['Trading']['change']:.2f}",
            f"{totals['Trading']['change_pct']:.2f}"
        ])
        
        # Write ISA Account totals
        writer.writerow([
            'ISA value GBP',
            f"{totals['ISA']['value']:.2f}",
            f"{totals['ISA']['change']:.2f}",
            f"{totals['ISA']['change_pct']:.2f}"
        ])
        
        # Write Grand Total Portfolio
        writer.writerow([
            'Grand Total Portfolio value GBP',
            f"{grand_total['value']:.2f}",
            f"{grand_total['change']:.2f}",
            f"{grand_total['change_pct']:.2f}"
        ])
        
        # Write Cash
        writer.writerow([
            'Grand Total cash GBP',
            f' {cash_gbp:.0f}',
            ' -',
            '-'
        ])
        
        # Write Total with cash
        writer.writerow([
            'Grand Total cash+portfolio value GVP',
            f' {total_with_cash:.0f}',
            '-',
            '-'
        ])
        
        # Separator
        writer.writerow(['--', '--', '--', '--'])
        
        # Percentages
        writer.writerow([f'% cash', f'{cash_pct:.2f}%', '', ''])
        writer.writerow([f'% portfolio', f'{portfolio_pct:.2f}%', '', ''])


def main():
    """Main function to calculate and write totals."""
    # Define paths
    project_root = Path(__file__).parent.parent
    input_path = project_root / 'source_of_truth' / 'source_of_truth.gbp.csv'
    output_path = project_root / 'source_of_truth' / 'totals_calc.csv'
    
    print(f"Reading from: {input_path}")
    
    # Calculate totals
    totals, grand_total = calculate_totals(input_path)
    
    # Write to CSV
    write_totals_csv(totals, grand_total, output_path)
    
    print(f"\nTotals calculated and saved to: {output_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Trading Account:")
    print(f"  Value: £{totals['Trading']['value']:.2f}")
    print(f"  Change: £{totals['Trading']['change']:.2f}")
    print(f"  Change %: {totals['Trading']['change_pct']:.2f}%")
    
    print(f"\nISA Account:")
    print(f"  Value: £{totals['ISA']['value']:.2f}")
    print(f"  Change: £{totals['ISA']['change']:.2f}")
    print(f"  Change %: {totals['ISA']['change_pct']:.2f}%")
    
    print(f"\nGrand Total:")
    print(f"  Value: £{grand_total['value']:.2f}")
    print(f"  Change: £{grand_total['change']:.2f}")
    print(f"  Change %: {grand_total['change_pct']:.2f}%")


if __name__ == "__main__":
    main()