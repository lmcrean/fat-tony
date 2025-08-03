import csv
import re
from pathlib import Path


def parse_currency_value(value_str):
    """Parse currency values with symbols and return (amount, currency)."""
    value_str = value_str.strip()
    
    # Handle percentage values
    if value_str.endswith('%'):
        return float(value_str.replace('%', '').replace('+', '')), '%'
    
    # Handle pence values
    if value_str.startswith('p'):
        return float(value_str[1:].replace(',', '')), 'GBX'
    
    # Handle dollar values
    if value_str.startswith('$'):
        return float(value_str[1:].replace(',', '')), 'USD'
    
    # Handle pound values - check for various encodings including replacement char
    # The pound symbol might be encoded differently or show as �
    if any(value_str.startswith(c) for c in ['£', '\xa3', '�', 'E']):
        # Remove the first character and any + or - signs
        cleaned = value_str[1:].replace(',', '').replace('+', '')
        return float(cleaned), 'GBP'
    
    # Also check if it contains a pound symbol or replacement char anywhere
    if any(c in value_str for c in ['£', '\xa3', '�']):
        # Remove all non-numeric characters except . and -
        cleaned = re.sub(r'[^0-9.-]', '', value_str)
        return float(cleaned), 'GBP'
    
    # Handle euro values
    if value_str.startswith('€'):
        return float(value_str[1:].replace(',', '')), 'EUR'
    
    # If no currency symbol, try to parse as float
    try:
        return float(value_str.replace(',', '').replace('+', '')), None
    except ValueError:
        raise ValueError(f"Cannot parse value: {value_str}")


def is_stock_name(line):
    """Check if a line is likely to be a stock name."""
    # Stock names don't start with numbers or currency symbols
    if not line or line[0].isdigit() or line.startswith(('$', '£', '€', 'p', '+', '-', 'E')):
        return False
    # Stock names don't look like pure numbers
    try:
        float(line.replace(',', ''))
        return False
    except ValueError:
        return True


def parse_markdown_data(file_path):
    """Parse the source_of_truth.md file and extract portfolio data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip() for line in f.readlines()]
    
    data = []
    current_account = None
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for account type headers
        if line == "## Trading Account (standard, GBP)":
            current_account = "Trading"
            i += 2  # Skip header and empty line
            continue
        elif line == "## Stocks and Shares ISA (GBP)":
            current_account = "ISA"
            i += 2  # Skip header and empty line
            continue
        
        # Skip empty lines and headers
        if not line or line.startswith('#') or not current_account:
            i += 1
            continue
        
        # Check if this line could be a stock name
        if not is_stock_name(line):
            i += 1
            continue
        
        # Try to parse a position entry
        name = line
        position_data = {'Name': name, 'Account Type': current_account}
        
        # Collect the next 6 lines as data values
        values = []
        j = i + 1
        while j < len(lines) and len(values) < 6:
            next_line = lines[j].strip()
            if next_line and not is_stock_name(next_line):
                values.append(next_line)
            elif is_stock_name(next_line):
                # We've hit the next stock name, stop collecting
                break
            j += 1
        
        # Parse the collected values
        if len(values) >= 6:
            try:
                # Parse each value
                position_data['Quantity'] = float(values[0])
                
                price_owned, price_currency = parse_currency_value(values[1])
                position_data['Price Owned'] = price_owned
                position_data['Price Currency'] = price_currency
                
                # For ISA "Shares China Large Cap", it seems to be missing current price
                # Check if the third value looks like a currency value or a current price
                if len(values) >= 3 and (values[2].startswith(('$', '£', '€', 'p')) or '.' in values[2]):
                    current_price, current_currency = parse_currency_value(values[2])
                    position_data['Current Price'] = current_price
                    position_data['Current Currency'] = current_currency or price_currency
                    value_idx = 3
                else:
                    # Missing current price, use price owned as current
                    position_data['Current Price'] = price_owned
                    position_data['Current Currency'] = price_currency
                    value_idx = 2
                
                # Parse remaining values
                if value_idx < len(values):
                    value_gbp, _ = parse_currency_value(values[value_idx])
                    position_data['Value (GBP)'] = value_gbp
                
                if value_idx + 1 < len(values):
                    change_gbp, _ = parse_currency_value(values[value_idx + 1])
                    position_data['Change (GBP)'] = change_gbp
                
                if value_idx + 2 < len(values):
                    change_pct, _ = parse_currency_value(values[value_idx + 2])
                    position_data['Change %'] = change_pct
                
                data.append(position_data)
                print(f"Parsed: {name} in {current_account} account")
                
            except (ValueError, IndexError) as e:
                print(f"Failed to parse {name}: {e}")
        
        # Move to the next potential stock name
        i = j if j < len(lines) else i + 1
    
    return data


def write_csv(data, output_path):
    """Write the parsed data to a CSV file."""
    if not data:
        print("No data to write!")
        return
    
    # Define the field names
    fieldnames = [
        'Account Type', 'Name', 'Quantity', 
        'Price Owned', 'Price Currency', 
        'Current Price', 'Current Currency',
        'Value (GBP)', 'Change (GBP)', 'Change %'
    ]
    
    # Fill in missing fields with empty values
    for row in data:
        for field in fieldnames:
            if field not in row:
                row[field] = ''
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def main():
    """Main function to parse markdown and create CSV."""
    # Define paths
    project_root = Path(__file__).parent.parent
    input_path = project_root / 'source_of_truth' / 'source_of_truth.md'
    output_path = project_root / 'source_of_truth' / 'source_of_truth.csv'
    
    print(f"Parsing: {input_path}")
    
    # Parse the markdown file
    data = parse_markdown_data(input_path)
    
    print(f"\nFound {len(data)} positions")
    
    # Write to CSV
    write_csv(data, output_path)
    
    print(f"CSV file created: {output_path}")
    
    # Print summary
    trading_positions = sum(1 for d in data if d['Account Type'] == 'Trading')
    isa_positions = sum(1 for d in data if d['Account Type'] == 'ISA')
    
    print(f"\nSummary:")
    print(f"  Trading Account positions: {trading_positions}")
    print(f"  ISA Account positions: {isa_positions}")
    print(f"  Total positions: {len(data)}")


if __name__ == "__main__":
    main()