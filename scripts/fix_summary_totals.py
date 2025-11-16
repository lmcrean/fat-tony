#!/usr/bin/env python3
"""
Quick script to recalculate summary totals from existing CSV without API calls.
Just sums the "Value (GBP)" column for each account type.
"""
import csv
from decimal import Decimal
from datetime import datetime

def recalculate_summary():
    """Read positions CSV and recalculate summary totals."""

    # Read existing positions
    positions_file = "output/portfolio_positions_FINAL.csv"

    isa_portfolio = Decimal('0')
    isa_result = Decimal('0')
    isa_cost_basis = Decimal('0')
    trading_portfolio = Decimal('0')
    trading_result = Decimal('0')
    trading_cost_basis = Decimal('0')

    with open(positions_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            account_type = row['Account Type']
            value_gbp = Decimal(row['Value (GBP)'].replace(',', ''))
            change_gbp = Decimal(row['Change (GBP)'].replace(',', '').replace('+', ''))

            # Cost basis = market value - profit/loss
            cost_basis = value_gbp - change_gbp

            if account_type == 'ISA':
                isa_portfolio += value_gbp
                isa_result += change_gbp
                isa_cost_basis += cost_basis
            else:  # Trading
                trading_portfolio += value_gbp
                trading_result += change_gbp
                trading_cost_basis += cost_basis

    # Read FREE FUNDS from existing summary (they are correct)
    summary_file = "output/portfolio_summary.csv"
    isa_free_funds = Decimal('0')
    trading_free_funds = Decimal('0')

    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'Stocks & Shares ISA' in line and ',' in line:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        isa_free_funds = Decimal(parts[1].replace(',', ''))
                elif 'Invest Account' in line and ',' in line:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        trading_free_funds = Decimal(parts[1].replace(',', ''))
    except Exception as e:
        print(f"Warning: Could not read FREE FUNDS from existing summary: {e}")

    # Generate new summary CSV
    csv_data = []
    csv_data.append([f"Trading 212 Portfolio Summary - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    csv_data.append([])
    csv_data.append(["ACCOUNT SUMMARIES"])
    csv_data.append(["ACCOUNT", "FREE_FUNDS", "PORTFOLIO", "RESULT", "CURRENCY"])

    csv_data.append([
        "Stocks & Shares ISA",
        f"{isa_free_funds:.2f}",
        f"{isa_portfolio:.2f}",
        f"{isa_result:+.2f}",
        "GBP"
    ])

    csv_data.append([
        "Invest Account",
        f"{trading_free_funds:.2f}",
        f"{trading_portfolio:.2f}",
        f"{trading_result:+.2f}",
        "GBP"
    ])

    # Combined totals
    total_free_funds = isa_free_funds + trading_free_funds
    total_portfolio = isa_portfolio + trading_portfolio
    total_result = isa_result + trading_result

    csv_data.append([])
    csv_data.append(["COMBINED TOTALS"])
    csv_data.append(["TOTAL_FREE_FUNDS", "TOTAL_PORTFOLIO", "TOTAL_RESULT", "CURRENCY"])
    csv_data.append([
        f"{total_free_funds:.2f}",
        f"{total_portfolio:.2f}",
        f"{total_result:+.2f}",
        "GBP"
    ])

    # Write to file
    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)

    # Also copy to web app
    import shutil
    import os
    web_summary = "apps/web/public/output/portfolio_summary.csv"
    if os.path.exists("apps/web"):
        os.makedirs(os.path.dirname(web_summary), exist_ok=True)
        shutil.copy2(summary_file, web_summary)
        print(f"[OK] Updated: {web_summary}")

    # Calculate result percentages
    isa_result_pct = (isa_result / isa_cost_basis * 100) if isa_cost_basis != 0 else Decimal('0')
    trading_result_pct = (trading_result / trading_cost_basis * 100) if trading_cost_basis != 0 else Decimal('0')
    total_cost_basis = isa_cost_basis + trading_cost_basis
    total_result_pct = (total_result / total_cost_basis * 100) if total_cost_basis != 0 else Decimal('0')

    print(f"[OK] Updated: {summary_file}")
    print(f"\nRecalculated totals:")
    print(f"ISA: £{isa_portfolio:.2f} portfolio, £{isa_result:+.2f} result ({isa_result_pct:+.2f}%)")
    print(f"Invest: £{trading_portfolio:.2f} portfolio, £{trading_result:+.2f} result ({trading_result_pct:+.2f}%)")
    print(f"Total: £{total_portfolio:.2f} portfolio, £{total_result:+.2f} result ({total_result_pct:+.2f}%)")

if __name__ == "__main__":
    recalculate_summary()
