import csv
from pathlib import Path
import re


def parse_currency_value(value_str):
    """Parse currency value from string, handling commas and spaces."""
    if not value_str or value_str.strip() in ['-', '--', '']:
        return None
    
    # Remove currency symbols and extra spaces, but keep digits, dots, and commas
    cleaned = re.sub(r'[£$\s]', '', str(value_str))
    # Remove commas used as thousand separators
    cleaned = cleaned.replace(',', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def calculate_percentages(csv_path):
    """Read totals_calc.csv and calculate cash and portfolio percentages."""
    cash_total = None
    portfolio_total = None
    total_combined = None
    
    # Read the CSV and extract required values
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
            
            if len(row) >= 2:
                account_type = row[0]
                
                if 'Grand Total Portfolio value GBP' in account_type:
                    portfolio_total = parse_currency_value(row[1])
                elif 'Grand Total cash GBP' in account_type:
                    # Cash value is split across columns due to comma: " 7" + "128.00"
                    cash_value_str = row[1] + "," + row[2] if len(row) > 2 else row[1]
                    cash_total = parse_currency_value(cash_value_str)
                elif 'Grand Total cash+portfolio value' in account_type:
                    total_combined = parse_currency_value(row[1])
    
    if cash_total is None or portfolio_total is None:
        print("Error: Could not find required cash and portfolio values")
        return None, None, rows
    
    # If total_combined is not found or is different from sum, calculate it
    if total_combined is None:
        total_combined = cash_total + portfolio_total
    
    # Calculate percentages
    cash_percentage = (cash_total / total_combined) * 100
    portfolio_percentage = (portfolio_total / total_combined) * 100
    
    print(f"Cash Total: £{cash_total:,.2f}")
    print(f"Portfolio Total: £{portfolio_total:,.2f}")
    print(f"Combined Total: £{total_combined:,.2f}")
    print(f"Cash Percentage: {cash_percentage:.2f}%")
    print(f"Portfolio Percentage: {portfolio_percentage:.2f}%")
    
    return cash_percentage, portfolio_percentage, rows


def update_csv_with_percentages(csv_path, cash_pct, portfolio_pct, rows):
    """Update the CSV file with calculated percentages."""
    if cash_pct is None or portfolio_pct is None:
        print("Error: Cannot update CSV with invalid percentages")
        return
    
    # Update the rows with calculated percentages
    updated_rows = []
    for row in rows:
        if len(row) >= 1:
            if row[0] == '% cash':
                # Replace empty % cash row with calculated value
                updated_row = ['% cash', f'{cash_pct:.2f}%', '', '']
                updated_rows.append(updated_row)
            elif row[0] == '% portfolio':
                # Replace empty % portfolio row with calculated value
                updated_row = ['% portfolio', f'{portfolio_pct:.2f}%', '', '']
                updated_rows.append(updated_row)
            else:
                updated_rows.append(row)
        else:
            updated_rows.append(row)
    
    # Write updated CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in updated_rows:
            writer.writerow(row)
    
    print(f"\nCSV updated successfully: {csv_path}")


def main():
    """Main function to calculate and update percentages."""
    # Define path
    project_root = Path(__file__).parent.parent
    csv_path = project_root / 'source_of_truth' / 'totals_calc.csv'
    
    print(f"Processing: {csv_path}")
    
    if not csv_path.exists():
        print(f"Error: File not found - {csv_path}")
        return
    
    # Calculate percentages
    cash_pct, portfolio_pct, rows = calculate_percentages(csv_path)
    
    if cash_pct is not None and portfolio_pct is not None:
        # Update CSV with calculated percentages
        update_csv_with_percentages(csv_path, cash_pct, portfolio_pct, rows)
        
        print("\nFinal Results:")
        print(f"Cash Allocation: {cash_pct:.2f}%")
        print(f"Portfolio Allocation: {portfolio_pct:.2f}%")
        print(f"Total: {cash_pct + portfolio_pct:.2f}%")
    else:
        print("Failed to calculate percentages")


if __name__ == "__main__":
    main()