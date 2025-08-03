import csv
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


# Exchange rates (approximate, as of August 2025)
EXCHANGE_RATES = {
    'USD': 0.787,  # 1 USD = 0.787 GBP
    'EUR': 0.833,  # 1 EUR = 0.833 GBP
    'GBX': 0.01,   # 1 pence = 0.01 GBP
    'GBP': 1.0     # 1 GBP = 1 GBP
}

# Ticker mappings for common stocks and ETFs
TICKER_MAPPINGS = {
    'Palantir': 'PLTR',
    'Nvidia': 'NVDA',
    'Rightmove': 'RMV.L',
    'Broadcom': 'AVGO',
    'Oracle': 'ORCL',
    'Shopify': 'SHOP',
    'iShares Physical Gold': 'SGLN.L',
    'Microsoft': 'MSFT',
    'Visa': 'V',
    'iShares Blockchain Technology': 'IBLC.L',
    'Spotify Technology': 'SPOT',
    'Meta Platforms': 'META',
    'iShares S&P 500 Information Technology Sector (Acc)': 'IITU.L',
    'VanEck Semiconductor (Acc)': 'SMH',
    'Mastercard': 'MA',
    'iShares Automation & Robotics (Dist)': 'RBOT.L',
    'Netflix': 'NFLX',
    'iShares Russell 1000 Growth': 'IWF',
    'Axon Enterprise': 'AXON',
    'WisdomTree Artificial Intelligence (Acc)': 'WTAI.L',
    'Alphabet (Class A)': 'GOOGL',
    'Vanguard Germany All Cap': 'VGEM.L',
    'iShares NASDAQ 100 (Acc)': 'CNX1.L',
    'Vanguard S&P 500 (Acc)': 'VUSA.L',
    'Uber Technologies': 'UBER',
    'Hims & Hers Health': 'HIMS',
    'Vanguard FTSE All-World (Acc)': 'VWRL.L',
    'Reddit': 'RDDT',
    'iShares China Large Cap (Acc)': 'IUKD.L',
    'MicroStrategy': 'MSTR',
    'ASML': 'ASML',
    'Amazon': 'AMZN',
    'Progressive': 'PGR',
    'Intuitive Surgical': 'ISRG',
    'Figma': 'FIGMA',  # Private company
    'Shares China Large Cap (Acc)': 'IUKD.L',
    'iShares Core DAX DE (Dist)': 'DAXE.L',
    'iShares MSCI India (Acc)': 'IIND.L'
}


def convert_to_gbp(amount: float, currency: str) -> float:
    """Convert amount to GBP using exchange rates."""
    if currency in EXCHANGE_RATES:
        return round(amount * EXCHANGE_RATES[currency], 2)
    return amount  # Return as-is if currency not found


def get_ticker(name: str) -> str:
    """Get ticker symbol for a given instrument name."""
    return TICKER_MAPPINGS.get(name, name.upper().replace(' ', '')[:8])


def parse_currency_value(value_str: str) -> Tuple[float, str]:
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
                quantity = float(values[0])
                
                price_owned, price_currency = parse_currency_value(values[1])
                
                # For ISA "Shares China Large Cap", it seems to be missing current price
                # Check if the third value looks like a currency value or a current price
                if len(values) >= 3 and (values[2].startswith(('$', '£', '€', 'p')) or '.' in values[2]):
                    current_price, current_currency = parse_currency_value(values[2])
                    value_idx = 3
                else:
                    # Missing current price, use price owned as current
                    current_price = price_owned
                    current_currency = price_currency
                    value_idx = 2
                
                # Parse remaining values
                value_gbp = 0
                change_gbp = 0
                change_pct = 0
                
                if value_idx < len(values):
                    value_gbp, _ = parse_currency_value(values[value_idx])
                
                if value_idx + 1 < len(values):
                    change_gbp, _ = parse_currency_value(values[value_idx + 1])
                
                if value_idx + 2 < len(values):
                    change_pct, _ = parse_currency_value(values[value_idx + 2])
                
                # Build position data with proper CSV format
                position_data = {
                    'Account Type': current_account,
                    'Name': name,
                    'Ticker': get_ticker(name),
                    'Quantity of Shares': quantity,
                    'Price owned Currency': price_currency or 'GBP',
                    'Current Price Currency': current_currency or price_currency or 'GBP',
                    'Price Owned': price_owned,
                    'Price Owned (GBP)': convert_to_gbp(price_owned, price_currency or 'GBP'),
                    'Current Price': current_price,
                    'Current Price (GBP)': convert_to_gbp(current_price, current_currency or price_currency or 'GBP'),
                    'Value (GBP)': value_gbp,
                    'Change (GBP)': change_gbp,
                    'Change %': change_pct
                }
                
                data.append(position_data)
                # Debug output for parsing
                print(f"Parsed: {name} ({get_ticker(name)}) in {current_account} account - £{value_gbp}")
                
            except (ValueError, IndexError) as e:
                print(f"Failed to parse {name}: {e} (values: {values})")
                # Continue parsing other positions even if one fails
        
        # Move to the next potential stock name
        i = j if j < len(lines) else i + 1
    
    return data


def write_csv(data, output_path):
    """Write the parsed data to a CSV file."""
    if not data:
        print("No data to write!")
        return
    
    # Define the exact field names as requested
    fieldnames = [
        'Account Type', 'Name', 'Ticker', 'Quantity of Shares',
        'Price owned Currency', 'Current Price Currency', 
        'Price Owned', 'Price Owned (GBP)', 
        'Current Price', 'Current Price (GBP)', 
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
    output_path = project_root / 'source_of_truth' / 'source_of_truth.gbp.csv'
    
    print(f"Parsing: {input_path}")
    
    # Parse the markdown file
    data = parse_markdown_data(input_path)
    
    print(f"\nFound {len(data)} positions")
    
    # Write to CSV
    write_csv(data, output_path)
    
    print(f"GBP CSV file created: {output_path}")
    
    # Print summary
    trading_positions = sum(1 for d in data if d['Account Type'] == 'Trading')
    isa_positions = sum(1 for d in data if d['Account Type'] == 'ISA')
    
    print(f"\nSummary:")
    print(f"  Trading Account positions: {trading_positions}")
    print(f"  ISA Account positions: {isa_positions}")
    print(f"  Total positions: {len(data)}")
    
    # Show sample of first few rows
    if data:
        print(f"\nSample data (first 3 positions):")
        for i, pos in enumerate(data[:3]):
            print(f"  {i+1}. {pos['Name']} ({pos['Ticker']}) - {pos['Account Type']} - £{pos['Value (GBP)']}")


if __name__ == "__main__":
    main()