#!/usr/bin/env python3
"""
Discrepancy Analysis Tool
Compares CSV export data with source of truth to identify biggest discrepancies
"""

import csv
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, NamedTuple, Optional
from dataclasses import dataclass


@dataclass
class Position:
    """Represents a portfolio position"""
    name: str
    account: str
    shares: Decimal
    avg_price: Decimal
    current_price: Decimal
    market_value: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal
    currency: str


@dataclass
class Discrepancy:
    """Represents a discrepancy between CSV and source of truth"""
    position_name: str
    field: str
    csv_value: Decimal
    source_value: Decimal
    difference: Decimal
    percentage_diff: Decimal
    severity: str


class DiscrepancyAnalyzer:
    def __init__(self):
        self.csv_positions = []
        self.source_positions = []
        self.discrepancies = []
        
    def parse_currency_value(self, value_str: str) -> Decimal:
        """Parse currency string to Decimal, handling various formats"""
        if not value_str:
            return Decimal('0')
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[£$€+,]', '', str(value_str).strip())
        # Handle percentage
        if '%' in cleaned:
            cleaned = cleaned.replace('%', '')
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')
    
    def load_csv_data(self, csv_path: str):
        """Load portfolio positions from CSV file"""
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Find the header line (contains ACCOUNT,NAME,SHARES...)
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
        
        for row in reader:
            if not row.get('NAME') or not row.get('ACCOUNT'):  # Skip empty rows
                continue
                
            position = Position(
                name=row['NAME'].strip(),
                account=row['ACCOUNT'].strip(),
                shares=self.parse_currency_value(row['SHARES']),
                avg_price=self.parse_currency_value(row['AVERAGE_PRICE']),
                current_price=self.parse_currency_value(row['CURRENT_PRICE']),
                market_value=self.parse_currency_value(row['MARKET_VALUE']),
                profit_loss=self.parse_currency_value(row['RESULT']),
                profit_loss_pct=self.parse_currency_value(row['RESULT_%']),
                currency=row['CURRENCY'].strip()
            )
            self.csv_positions.append(position)
    
    def parse_source_of_truth(self, source_path: str):
        """Parse the manual source of truth markdown file"""
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse Trading Account positions
        trading_section = re.search(r'## Trading Account.*?(?=## Stocks and Shares ISA|\Z)', content, re.DOTALL)
        if trading_section:
            self._parse_trading_positions(trading_section.group(), "Invest Account")
        
        # Parse ISA positions  
        isa_section = re.search(r'## Stocks and Shares ISA.*', content, re.DOTALL)
        if isa_section:
            self._parse_isa_positions(isa_section.group(), "Stocks & Shares ISA")
    
    def _parse_trading_positions(self, section: str, account: str):
        """Parse individual trading account positions"""
        lines = section.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and not line.startswith('#') and not line.startswith('Name'):
                # Position name
                name = line
                if i + 6 < len(lines):
                    try:
                        shares = self.parse_currency_value(lines[i + 1])
                        avg_price_str = lines[i + 2].strip()
                        current_price_str = lines[i + 3].strip()
                        market_value = self.parse_currency_value(lines[i + 4])
                        profit_loss = self.parse_currency_value(lines[i + 5])
                        profit_loss_pct = self.parse_currency_value(lines[i + 6])
                        
                        # Parse prices handling currency symbols
                        avg_price = self._parse_price(avg_price_str)
                        current_price = self._parse_price(current_price_str)
                        
                        position = Position(
                            name=name,
                            account=account,
                            shares=shares,
                            avg_price=avg_price,
                            current_price=current_price,
                            market_value=market_value,
                            profit_loss=profit_loss,
                            profit_loss_pct=profit_loss_pct,
                            currency="GBP"
                        )
                        self.source_positions.append(position)
                        i += 7
                    except Exception as e:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
    
    def _parse_isa_positions(self, section: str, account: str):
        """Parse ISA positions with their specific formatting"""
        # Extract individual position blocks
        positions = re.findall(r'\*\*(.*?)\*\*\n\n(.*?)(?=\*\*|\Z)', section, re.DOTALL)
        
        for name, details in positions:
            lines = [line.strip() for line in details.split('\n') if line.strip()]
            if len(lines) >= 6:
                try:
                    shares = self.parse_currency_value(lines[0])
                    avg_price = self._parse_price(lines[1])
                    current_price = self._parse_price(lines[2])
                    market_value = self.parse_currency_value(lines[3])
                    profit_loss = self.parse_currency_value(lines[4])
                    profit_loss_pct = self.parse_currency_value(lines[5])
                    
                    position = Position(
                        name=name,
                        account=account,
                        shares=shares,
                        avg_price=avg_price,
                        current_price=current_price,
                        market_value=market_value,
                        profit_loss=profit_loss,
                        profit_loss_pct=profit_loss_pct,
                        currency="GBP"
                    )
                    self.source_positions.append(position)
                except Exception as e:
                    continue
    
    def _parse_price(self, price_str: str) -> Decimal:
        """Parse price handling different currency formats"""
        if not price_str:
            return Decimal('0')
        
        # Handle pence notation (p2,827.00 -> 28.27)
        if price_str.startswith('p'):
            pence_value = self.parse_currency_value(price_str[1:])
            return pence_value / 100
        
        # Handle other currency formats
        return self.parse_currency_value(price_str)
    
    def find_matching_position(self, csv_pos: Position) -> Optional[Position]:
        """Find matching position in source of truth"""
        # Try exact name match first
        for source_pos in self.source_positions:
            if source_pos.name == csv_pos.name and source_pos.account == csv_pos.account:
                return source_pos
        
        # Try partial name matching
        for source_pos in self.source_positions:
            if (source_pos.name.lower() in csv_pos.name.lower() or 
                csv_pos.name.lower() in source_pos.name.lower()) and source_pos.account == csv_pos.account:
                return source_pos
        
        return None
    
    def calculate_discrepancies(self):
        """Calculate discrepancies between CSV and source of truth"""
        self.discrepancies = []
        
        for csv_pos in self.csv_positions:
            source_pos = self.find_matching_position(csv_pos)
            if source_pos:
                # Compare market values
                mv_diff = csv_pos.market_value - source_pos.market_value
                if abs(mv_diff) > Decimal('0.10'):  # More than 10p difference
                    mv_pct_diff = (mv_diff / source_pos.market_value * 100) if source_pos.market_value > 0 else Decimal('0')
                    severity = self._get_severity(abs(mv_pct_diff))
                    
                    self.discrepancies.append(Discrepancy(
                        position_name=csv_pos.name,
                        field="market_value",
                        csv_value=csv_pos.market_value,
                        source_value=source_pos.market_value,
                        difference=mv_diff,
                        percentage_diff=mv_pct_diff,
                        severity=severity
                    ))
                
                # Compare profit/loss
                pl_diff = csv_pos.profit_loss - source_pos.profit_loss
                if abs(pl_diff) > Decimal('0.10'):
                    pl_pct_diff = (pl_diff / abs(source_pos.profit_loss) * 100) if source_pos.profit_loss != 0 else Decimal('0')
                    severity = self._get_severity(abs(pl_pct_diff))
                    
                    self.discrepancies.append(Discrepancy(
                        position_name=csv_pos.name,
                        field="profit_loss",
                        csv_value=csv_pos.profit_loss,
                        source_value=source_pos.profit_loss,
                        difference=pl_diff,
                        percentage_diff=pl_pct_diff,
                        severity=severity
                    ))
        
        # Check for missing positions
        self._check_missing_positions()
    
    def _get_severity(self, pct_diff: Decimal) -> str:
        """Determine severity based on percentage difference"""
        if pct_diff > 50:
            return "CRITICAL"
        elif pct_diff > 20:
            return "HIGH"
        elif pct_diff > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _check_missing_positions(self):
        """Check for positions in source of truth but missing from CSV"""
        for source_pos in self.source_positions:
            found = False
            for csv_pos in self.csv_positions:
                if (source_pos.name.lower() in csv_pos.name.lower() or 
                    csv_pos.name.lower() in source_pos.name.lower()) and source_pos.account == csv_pos.account:
                    found = True
                    break
            
            if not found and source_pos.market_value > Decimal('10'):  # Only flag if value > £10
                self.discrepancies.append(Discrepancy(
                    position_name=source_pos.name,
                    field="missing_position",
                    csv_value=Decimal('0'),
                    source_value=source_pos.market_value,
                    difference=-source_pos.market_value,
                    percentage_diff=Decimal('-100'),
                    severity="CRITICAL"
                ))
    
    def generate_report(self) -> str:
        """Generate detailed discrepancy report"""
        report = []
        report.append("# Portfolio Discrepancy Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        total_csv_value = sum(pos.market_value for pos in self.csv_positions)
        total_source_value = sum(pos.market_value for pos in self.source_positions)
        total_difference = total_csv_value - total_source_value
        total_pct_diff = (total_difference / total_source_value * 100) if total_source_value > 0 else Decimal('0')
        
        report.append("## Executive Summary")
        report.append(f"CSV Total Portfolio Value: £{total_csv_value:,.2f}")
        report.append(f"Source of Truth Total: £{total_source_value:,.2f}")
        report.append(f"**Total Discrepancy: £{total_difference:,.2f} ({total_pct_diff:+.2f}%)**")
        report.append("")
        
        # Severity breakdown
        severity_counts = {}
        for disc in self.discrepancies:
            severity_counts[disc.severity] = severity_counts.get(disc.severity, 0) + 1
        
        report.append("## Discrepancy Severity Breakdown")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            report.append(f"- {severity}: {count} issues")
        report.append("")
        
        # Top discrepancies by financial impact
        sorted_discrepancies = sorted(self.discrepancies, key=lambda x: abs(x.difference), reverse=True)
        
        report.append("## Top 10 Discrepancies by Financial Impact")
        report.append("| Position | Field | CSV Value | Source Value | Difference | % Diff | Severity |")
        report.append("|----------|-------|-----------|--------------|------------|--------|----------|")
        
        for i, disc in enumerate(sorted_discrepancies[:10]):
            report.append(f"| {disc.position_name[:30]} | {disc.field} | £{disc.csv_value:.2f} | £{disc.source_value:.2f} | £{disc.difference:+.2f} | {disc.percentage_diff:+.2f}% | {disc.severity} |")
        
        report.append("")
        
        # Account-level analysis
        report.append("## Account-Level Analysis")
        
        accounts = set(pos.account for pos in self.csv_positions + self.source_positions)
        for account in accounts:
            csv_account_total = sum(pos.market_value for pos in self.csv_positions if pos.account == account)
            source_account_total = sum(pos.market_value for pos in self.source_positions if pos.account == account)
            account_diff = csv_account_total - source_account_total
            
            report.append(f"### {account}")
            report.append(f"- CSV Total: £{csv_account_total:,.2f}")
            report.append(f"- Source Total: £{source_account_total:,.2f}")
            report.append(f"- Difference: £{account_diff:+,.2f}")
            report.append("")
        
        # Critical issues requiring immediate attention
        critical_issues = [d for d in self.discrepancies if d.severity == "CRITICAL"]
        if critical_issues:
            report.append("## 🚨 Critical Issues Requiring Immediate Attention")
            for issue in critical_issues:
                report.append(f"- **{issue.position_name}** ({issue.field}): £{issue.difference:+.2f} difference ({issue.percentage_diff:+.2f}%)")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main function to run the discrepancy analysis"""
    analyzer = DiscrepancyAnalyzer()
    
    # Load CSV data
    print("Loading CSV data...")
    analyzer.load_csv_data("portfolio_positions.csv")
    
    # Load source of truth
    print("Loading source of truth data...")
    analyzer.parse_source_of_truth("source_of_truth/source_of_truth.md")
    
    # Calculate discrepancies
    print("Calculating discrepancies...")
    analyzer.calculate_discrepancies()
    
    # Generate report
    print("Generating report...")
    report = analyzer.generate_report()
    
    # Save report
    with open("discrepancy_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Analysis complete! Found {len(analyzer.discrepancies)} discrepancies.")
    print("Report saved to: discrepancy_report.md")
    
    # Print top 5 issues to console
    sorted_discrepancies = sorted(analyzer.discrepancies, key=lambda x: abs(x.difference), reverse=True)
    print("\nTop 5 Biggest Discrepancies:")
    for i, disc in enumerate(sorted_discrepancies[:5]):
        print(f"{i+1}. {disc.position_name} ({disc.field}): £{disc.difference:+.2f} ({disc.percentage_diff:+.2f}%)")


if __name__ == "__main__":
    main()