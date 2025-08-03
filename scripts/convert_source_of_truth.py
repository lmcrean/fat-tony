#!/usr/bin/env python3
"""
Convert source_of_truth.md to a structured JSON format for easier comparison
"""

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional


def parse_price(price_str: str) -> Dict[str, Any]:
    """Parse price string and extract value, currency, and original format"""
    price_str = price_str.strip()
    
    # Handle pence notation (p543.0)
    if price_str.startswith('p'):
        value_str = price_str[1:].replace(',', '')
        return {
            "value": float(value_str),
            "currency": "GBX",
            "original_format": price_str
        }
    
    # Handle pound sterling (£30.899)
    elif price_str.startswith('£'):
        value_str = price_str[1:].replace(',', '')
        return {
            "value": float(value_str),
            "currency": "GBP",
            "original_format": price_str
        }
    
    # Handle dollars ($93.82)
    elif price_str.startswith('$'):
        value_str = price_str[1:].replace(',', '')
        return {
            "value": float(value_str),
            "currency": "USD",
            "original_format": price_str
        }
    
    # Handle euros (€4.3521)
    elif price_str.startswith('€'):
        value_str = price_str[1:].replace(',', '')
        return {
            "value": float(value_str),
            "currency": "EUR",
            "original_format": price_str
        }
    
    # Handle typo E160.24 -> should be £160.24
    elif price_str.startswith('E') and len(price_str) > 1 and price_str[1].isdigit():
        value_str = price_str[1:].replace(',', '')
        return {
            "value": float(value_str),
            "currency": "GBP",
            "original_format": price_str,
            "note": "Typo corrected from E to £"
        }
    
    # Default case - no currency symbol
    else:
        return {
            "value": float(price_str.replace(',', '')),
            "currency": "UNKNOWN",
            "original_format": price_str
        }


def parse_value(value_str: str) -> float:
    """Parse value string removing currency symbols and converting to float"""
    # Handle E typo (E160.24 should be £160.24)
    if value_str.startswith('E') and len(value_str) > 1 and value_str[1].isdigit():
        value_str = '£' + value_str[1:]
    
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[£$€+,]', '', value_str.strip())
    # Handle percentage
    cleaned = cleaned.replace('%', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_trading_account_positions(content: str) -> List[Dict[str, Any]]:
    """Parse Trading Account section positions"""
    positions = []
    
    # Find Trading Account section
    trading_match = re.search(r'## Trading Account.*?(?=## Stocks and Shares ISA|\Z)', content, re.DOTALL)
    if not trading_match:
        return positions
    
    section = trading_match.group()
    lines = section.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines, headers, and structural text
        if (not line or line.startswith('#') or 
            line.startswith('Name') or line.startswith('below was') or
            line.startswith('structure of data')):
            i += 1
            continue
        
        # Try to parse a position (7 lines per position)
        if i + 6 < len(lines):
            try:
                position = {
                    "name": line,
                    "quantity": parse_value(lines[i + 1]),
                    "avg_price": parse_price(lines[i + 2].strip()),
                    "current_price": parse_price(lines[i + 3].strip()),
                    "market_value_gbp": parse_value(lines[i + 4]),
                    "profit_loss_gbp": parse_value(lines[i + 5]),
                    "profit_loss_pct": parse_value(lines[i + 6])
                }
                positions.append(position)
                i += 7
            except Exception as e:
                print(f"Error parsing position at line {i}: {e}")
                i += 1
        else:
            i += 1
    
    return positions


def parse_isa_account_positions(content: str) -> List[Dict[str, Any]]:
    """Parse ISA Account section positions"""
    positions = []
    
    # Find ISA section
    isa_match = re.search(r'## Stocks and Shares ISA.*', content, re.DOTALL)
    if not isa_match:
        return positions
    
    section = isa_match.group()
    
    # Parse positions without ** markers first (new format)
    # Figma - no markers
    figma_match = re.search(r'Figma\n([\d.]+)\n(\$[\d.]+)\n(\$[\d.]+)\n(£[\d.]+)\n(\+£[\d.]+)\n(\+[\d.]+%)', section)
    if figma_match:
        positions.append({
            "name": "Figma",
            "quantity": parse_value(figma_match.group(1)),
            "avg_price": parse_price(figma_match.group(2)),
            "current_price": parse_price(figma_match.group(3)),
            "market_value_gbp": parse_value(figma_match.group(4)),
            "profit_loss_gbp": parse_value(figma_match.group(5)),
            "profit_loss_pct": parse_value(figma_match.group(6))
        })
    
    # Alphabet - no markers, has E160.24 typo
    alphabet_match = re.search(r'Alphabet \(Class A\)\n([\d.]+)\n(\$[\d.]+)\n(\$[\d.]+)\n(E[\d.]+)\n(\+[\d.]+%)\n(\+£[\d.]+)', section)
    if alphabet_match:
        positions.append({
            "name": "Alphabet (Class A)",
            "quantity": parse_value(alphabet_match.group(1)),
            "avg_price": parse_price(alphabet_match.group(2)),
            "current_price": parse_price(alphabet_match.group(3)),
            "market_value_gbp": parse_value(alphabet_match.group(4)),
            "profit_loss_gbp": parse_value(alphabet_match.group(6)),
            "profit_loss_pct": parse_value(alphabet_match.group(5))
        })
    
    # Vanguard S&P 500 - no markers
    vanguard_match = re.search(r'Vanguard S&P 500 \(Acc\)\n([\d.]+)\n(£[\d.]+)\n(£[\d.]+)\n(£[\d.,]+)\n(\+£[\d.]+)\n(\+[\d.]+%)', section)
    if vanguard_match:
        positions.append({
            "name": "Vanguard S&P 500 (Acc)",
            "quantity": parse_value(vanguard_match.group(1)),
            "avg_price": parse_price(vanguard_match.group(2)),
            "current_price": parse_price(vanguard_match.group(3)),
            "market_value_gbp": parse_value(vanguard_match.group(4)),
            "profit_loss_gbp": parse_value(vanguard_match.group(5)),
            "profit_loss_pct": parse_value(vanguard_match.group(6))
        })
    
    # Shares China Large Cap - no markers, missing avg price
    china_match = re.search(r'Shares China Large Cap \(Acc\)\n([\d.]+)\n(€[\d.]+)\n(£[\d.,]+)\n(\+£[\d.]+)\n(\+[\d.]+%)', section)
    if china_match:
        positions.append({
            "name": "iShares China Large Cap (Acc)",
            "quantity": parse_value(china_match.group(1)),
            "avg_price": None,  # Missing in source
            "current_price": parse_price(china_match.group(2)),
            "market_value_gbp": parse_value(china_match.group(3)),
            "profit_loss_gbp": parse_value(china_match.group(4)),
            "profit_loss_pct": parse_value(china_match.group(5))
        })
    
    # iShares Core DAX DE - no markers
    dax_match = re.search(r'iShares Core DAX DE \(Dist\)\n([\d.]+)\n(€[\d.]+)\n(€[\d.]+)\n(£[\d.]+)\n(\+£[\d.]+)\n(\+[\d.]+%)', section)
    if dax_match:
        positions.append({
            "name": "iShares Core DAX DE (Dist)",
            "quantity": parse_value(dax_match.group(1)),
            "avg_price": parse_price(dax_match.group(2)),
            "current_price": parse_price(dax_match.group(3)),
            "market_value_gbp": parse_value(dax_match.group(4)),
            "profit_loss_gbp": parse_value(dax_match.group(5)),
            "profit_loss_pct": parse_value(dax_match.group(6))
        })
    
    # iShares MSCI India - no markers
    india_match = re.search(r'iShares MSCI India \(Acc\)\n([\d.]+)\n(£[\d.]+)\n(£[\d.]+)\n(£[\d.]+)\n(-£[\d.]+)\n(-[\d.]+%)', section)
    if india_match:
        positions.append({
            "name": "iShares MSCI India (Acc)",
            "quantity": parse_value(india_match.group(1)),
            "avg_price": parse_price(india_match.group(2)),
            "current_price": parse_price(india_match.group(3)),
            "market_value_gbp": parse_value(india_match.group(4)),
            "profit_loss_gbp": parse_value(india_match.group(5)),
            "profit_loss_pct": parse_value(india_match.group(6))
        })
    
    return positions


def calculate_totals(positions: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate account totals"""
    total_market_value = sum(pos["market_value_gbp"] for pos in positions)
    total_profit_loss = sum(pos["profit_loss_gbp"] for pos in positions)
    
    # Calculate weighted average profit/loss percentage
    total_invested = 0
    for pos in positions:
        if pos["profit_loss_gbp"] != 0:
            invested = pos["market_value_gbp"] - pos["profit_loss_gbp"]
            total_invested += invested
    
    total_profit_loss_pct = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
    
    return {
        "total_market_value_gbp": round(total_market_value, 2),
        "total_profit_loss_gbp": round(total_profit_loss, 2),
        "total_profit_loss_pct": round(total_profit_loss_pct, 2),
        "position_count": len(positions)
    }


def main():
    # Read source of truth markdown
    source_path = Path("source_of_truth/source_of_truth.md")
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse positions
    trading_positions = parse_trading_account_positions(content)
    isa_positions = parse_isa_account_positions(content)
    
    # Build JSON structure
    data = {
        "metadata": {
            "date": "2025-08-01",
            "source": "Trading 212 mobile app manual copy",
            "format_version": "1.0"
        },
        "accounts": {
            "trading_account": {
                "name": "Trading Account (standard, GBP)",
                "positions": trading_positions,
                "totals": calculate_totals(trading_positions)
            },
            "isa_account": {
                "name": "Stocks and Shares ISA (GBP)",
                "positions": isa_positions,
                "totals": calculate_totals(isa_positions)
            }
        },
        "portfolio_totals": {
            "total_market_value_gbp": round(
                calculate_totals(trading_positions)["total_market_value_gbp"] +
                calculate_totals(isa_positions)["total_market_value_gbp"], 2
            ),
            "total_profit_loss_gbp": round(
                calculate_totals(trading_positions)["total_profit_loss_gbp"] +
                calculate_totals(isa_positions)["total_profit_loss_gbp"], 2
            ),
            "total_positions": len(trading_positions) + len(isa_positions)
        }
    }
    
    # Save JSON
    output_path = Path("source_of_truth/source_of_truth.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"Converted {len(trading_positions)} Trading Account positions")
    print(f"Converted {len(isa_positions)} ISA Account positions")
    print(f"Total portfolio value: £{data['portfolio_totals']['total_market_value_gbp']:,.2f}")
    print(f"Total profit/loss: £{data['portfolio_totals']['total_profit_loss_gbp']:,.2f}")
    print(f"\nJSON file saved to: {output_path}")


if __name__ == "__main__":
    main()