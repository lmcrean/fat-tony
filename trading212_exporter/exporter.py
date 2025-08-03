"""
Portfolio data processing and markdown generation.
"""

import csv
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from tabulate import tabulate

from .models import Position, AccountSummary
from .client import Trading212Client
from .ticker_mappings import get_display_name


class PortfolioExporter:
    """Handles portfolio data processing and markdown generation."""
    
    def __init__(self, clients: Dict[str, Trading212Client]):
        """Initialize the exporter with Trading 212 clients."""
        # Support both single client (backward compatibility) and multiple clients
        if isinstance(clients, Trading212Client):
            # Backward compatibility: single client
            self.clients = {"Trading 212": clients}
        else:
            # New format: dictionary of clients
            self.clients = clients
        
        self.positions: List[Position] = []
        self.account_summaries: Dict[str, AccountSummary] = {}
    
    
    def fetch_data(self):
        """Fetch all necessary data from the API."""
        print("Fetching portfolio data from all accounts...")
        
        for account_name, client in self.clients.items():
            print(f"\n--- Fetching data for {account_name} ---")
            
            # Get account metadata for currency (optional - may fail due to API permissions)
            try:
                metadata = client.get_account_metadata()
                account_currency = metadata.get('currencyCode', 'GBP')
                print(f"Account currency: {account_currency}")
            except Exception as e:
                print(f"Could not fetch account metadata (API permissions): {e}")
                account_currency = 'GBP'  # Default currency when account access is restricted
            
            # Get portfolio positions
            portfolio_data = client.get_portfolio()
            print(f"Found {len(portfolio_data)} positions in {account_name}")
            
            # Log all tickers for debugging
            tickers = [p['ticker'] for p in portfolio_data]
            print(f"Tickers: {', '.join(tickers)}")
            
            # Process each position
            for position_data in portfolio_data:
                ticker = position_data['ticker']
                
                # Get detailed position info
                print(f"Fetching details for {ticker}...")
                api_name = None
                try:
                    details = client.get_position_details(ticker)
                    api_name = details.get('name', ticker)
                except Exception as e:
                    print(f"Warning: Could not fetch details for {ticker}: {e}")
                    print(f"Using ticker mapping for display name")
                
                # Use the ticker mapping to get a proper display name
                display_name = get_display_name(ticker, api_name)
                print(f"  -> Using display name: {display_name}")
                
                # Get raw price data (no conversion)
                avg_price = Decimal(str(position_data['averagePrice']))
                current_price = Decimal(str(position_data['currentPrice']))
                
                position = Position(
                    ticker=ticker,
                    name=display_name,
                    shares=Decimal(str(position_data['quantity'])),
                    average_price=avg_price,
                    current_price=current_price,
                    currency=position_data.get('currencyCode', account_currency),
                    account_name=account_name
                )
                self.positions.append(position)
            
            # Get cash balance (optional - may fail due to API permissions)
            print("Fetching cash balance...")
            try:
                cash_data = client.get_account_cash()
                free_funds = Decimal(str(cash_data.get('free', 0)))
            except Exception as e:
                print(f"Could not fetch cash balance (API permissions): {e}")
                free_funds = Decimal('0')  # Default when account access is restricted
            
            # Calculate summary for this account
            account_positions = [p for p in self.positions if p.account_name == account_name]
            total_invested = sum(p.cost_basis for p in account_positions)
            total_value = sum(p.market_value for p in account_positions)
            total_result = total_value - total_invested
            
            self.account_summaries[account_name] = AccountSummary(
                free_funds=free_funds,
                invested=Decimal(str(total_value)),
                result=Decimal(str(total_result)),
                currency=account_currency,
                account_name=account_name
            )
    
    def _format_currency(self, value: Decimal, currency: str = "GBP") -> str:
        """Format a decimal value as currency."""
        symbol = "£" if currency == "GBP" else currency
        return f"{symbol}{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
    
    def _format_percentage(self, value: Decimal) -> str:
        """Format a decimal value as percentage with color indicator."""
        formatted = f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):+.2f}%"
        
        if value > 0:
            return f"🟢 {formatted}"
        elif value < 0:
            return f"🔴 {formatted}"
        else:
            return f"⚪ {formatted}"
    
    def _format_profit_loss(self, value: Decimal, currency: str = "GBP") -> str:
        """Format profit/loss with color indicator."""
        formatted = self._format_currency(value, currency)
        
        if value > 0:
            return f"🟢 {formatted}"
        elif value < 0:
            return f"🔴 {formatted}"
        else:
            return f"⚪ {formatted}"
    
    def _format_currency_csv(self, value: Decimal, currency: str = "GBP") -> str:
        """Format a decimal value as currency for CSV (no symbols)."""
        return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
    
    def _format_percentage_csv(self, value: Decimal) -> str:
        """Format a decimal value as percentage for CSV (no color indicators)."""
        return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):+.2f}%"
    
    def _format_profit_loss_csv(self, value: Decimal) -> str:
        """Format profit/loss for CSV (no color indicators)."""
        return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):+,.2f}"
    
    def _format_price_raw(self, value: Decimal) -> str:
        """Format a price value without currency symbols for CSV."""
        return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
    
    def _detect_actual_currency(self, ticker: str, price: Decimal, reported_currency: str) -> str:
        """Detect the actual currency based on ticker symbol and price patterns.
        
        Trading 212 API sometimes reports incorrect currency codes, so we need
        to infer the actual currency from the ticker and price ranges.
        """
        # US stocks ending in _US_EQ are typically in USD
        if ticker.endswith('_US_EQ'):
            return 'USD'
        
        # European ETFs - check these first before UK ETF catch-all
        if ('DAX' in ticker or ticker.endswith('d_EQ') or 
            'FXAC' in ticker or 'EXIC' in ticker):
            return 'EUR'
        
        # UK ETFs ending in .L or non-US _EQ are typically in GBX/GBP
        if ticker.endswith('.L') or (ticker.endswith('_EQ') and not ticker.endswith('_US_EQ')):
            # Large values (>1000) are likely in pence for UK instruments
            if price > Decimal('1000'):
                return 'GBX'
            # Special cases for UK stocks that trade in hundreds of pence
            elif 'RMV' in ticker and price > Decimal('500'):
                return 'GBX'
            else:
                return 'GBP'
        
        # Default to reported currency
        return reported_currency
    
    def _convert_to_gbp(self, value: Decimal, currency: str, ticker: str = "") -> Decimal:
        """Convert currency value to GBP equivalent.
        
        Uses realistic conversion rates based on typical exchange rates:
        - GBP: return as-is
        - GBX (pence): divide by 100
        - USD: multiply by ~0.79 (typical USD/GBP rate)
        - EUR: multiply by ~0.86 (typical EUR/GBP rate)
        """
        # Detect actual currency if needed
        actual_currency = self._detect_actual_currency(ticker, value, currency)
        
        if actual_currency == "GBP":
            return value
        elif actual_currency == "GBX":
            return value / Decimal('100')
        elif actual_currency == "USD":
            # Approximate USD to GBP conversion (varies over time)
            # Using a realistic rate around 0.79
            return value * Decimal('0.79')
        elif actual_currency == "EUR":
            # Approximate EUR to GBP conversion
            # Using a realistic rate around 0.86
            return value * Decimal('0.86')
        else:
            # For other currencies, assume GBP equivalent
            return value
    
    def generate_markdown(self) -> str:
        """Generate the markdown output."""
        lines = []
        
        # Header
        lines.append("# Trading 212 Portfolio")
        lines.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Check if we have multiple accounts
        if len(self.clients) > 1:
            # Multi-account view: separate sections for each account
            for account_name in self.clients.keys():
                lines.append(f"## {account_name}\n")
                
                # Account-specific positions
                account_positions = [p for p in self.positions if p.account_name == account_name]
                if account_positions:
                    table_data = []
                    for position in sorted(account_positions, key=lambda p: p.market_value, reverse=True):
                        table_data.append([
                            position.name,
                            f"{position.shares:,.4f}".rstrip('0').rstrip('.'),
                            self._format_currency(position.average_price, position.currency),
                            self._format_currency(position.current_price, position.currency),
                            self._format_currency(position.market_value, position.currency),
                            self._format_profit_loss(position.profit_loss, position.currency),
                            self._format_percentage(position.profit_loss_percent)
                        ])
                    
                    headers = ["NAME", "SHARES", "AVERAGE PRICE", "CURRENT PRICE", "MARKET VALUE", "RESULT", "RESULT %"]
                    
                    # Generate table with right-aligned numeric columns
                    table = tabulate(
                        table_data,
                        headers=headers,
                        tablefmt="pipe",
                        numalign="right",
                        stralign="left"
                    )
                    
                    lines.append("### Positions\n")
                    lines.append(table)
                
                # Account summary
                if account_name in self.account_summaries:
                    summary = self.account_summaries[account_name]
                    lines.append("\n### Summary\n")
                    summary_data = [
                        ["FREE FUNDS", self._format_currency(summary.free_funds, summary.currency)],
                        ["PORTFOLIO", self._format_currency(summary.invested, summary.currency)],
                        ["RESULT", self._format_profit_loss(summary.result, summary.currency)]
                    ]
                    
                    summary_table = tabulate(
                        summary_data,
                        tablefmt="pipe",
                        numalign="right"
                    )
                    lines.append(summary_table)
                
                lines.append("\n---\n")
            
            # Combined totals (if all accounts use same currency)
            currencies = set(summary.currency for summary in self.account_summaries.values())
            if len(currencies) == 1:
                currency = currencies.pop()
                total_free_funds = sum(s.free_funds for s in self.account_summaries.values())
                total_invested = sum(s.invested for s in self.account_summaries.values())
                total_result = sum(s.result for s in self.account_summaries.values())
                
                lines.append("## Combined Totals\n")
                combined_data = [
                    ["TOTAL FREE FUNDS", self._format_currency(total_free_funds, currency)],
                    ["TOTAL PORTFOLIO", self._format_currency(total_invested, currency)],
                    ["TOTAL RESULT", self._format_profit_loss(total_result, currency)]
                ]
                
                combined_table = tabulate(
                    combined_data,
                    tablefmt="pipe",
                    numalign="right"
                )
                lines.append(combined_table)
        else:
            # Single account view (backward compatibility)
            # Portfolio table
            table_data = []
            for position in sorted(self.positions, key=lambda p: p.market_value, reverse=True):
                table_data.append([
                    position.name,
                    f"{position.shares:,.4f}".rstrip('0').rstrip('.'),
                    self._format_currency(position.average_price, position.currency),
                    self._format_currency(position.current_price, position.currency),
                    self._format_currency(position.market_value, position.currency),
                    self._format_profit_loss(position.profit_loss, position.currency),
                    self._format_percentage(position.profit_loss_percent)
                ])
            
            headers = ["NAME", "SHARES", "AVERAGE PRICE", "CURRENT PRICE", "MARKET VALUE", "RESULT", "RESULT %"]
            
            # Generate table with right-aligned numeric columns
            table = tabulate(
                table_data,
                headers=headers,
                tablefmt="pipe",
                numalign="right",
                stralign="left"
            )
            
            lines.append("## Portfolio Positions\n")
            lines.append(table)
            
            # Summary section
            account_name = list(self.account_summaries.keys())[0]
            if account_name in self.account_summaries:
                summary = self.account_summaries[account_name]
                lines.append("\n## Summary\n")
                summary_data = [
                    ["FREE FUNDS", self._format_currency(summary.free_funds, summary.currency)],
                    ["PORTFOLIO", self._format_currency(summary.invested, summary.currency)],
                    ["RESULT", self._format_profit_loss(summary.result, summary.currency)]
                ]
                
                summary_table = tabulate(
                    summary_data,
                    tablefmt="pipe",
                    numalign="right"
                )
                lines.append(summary_table)
        
        return "\n".join(lines)
    
    def generate_positions_csv(self) -> List[List[str]]:
        """Generate CSV data for positions matching source_of_truth.gbp.csv format exactly."""
        csv_data = []
        
        # Header matching source_of_truth.gbp.csv format exactly
        csv_data.append(["Account Type", "Name", "Ticker", "Quantity of Shares", "Price owned Currency", "Current Price Currency", "Price Owned", "Price Owned (GBP)", "Current Price", "Current Price (GBP)", "Value (GBP)", "Change (GBP)", "Change %"])
        
        # Process all positions
        for position in sorted(self.positions, key=lambda p: p.market_value, reverse=True):
            # Map account names to match source_of_truth format
            account_type = "ISA" if "ISA" in position.account_name else "Trading"
            
            # Detect actual currencies and calculate GBP equivalent prices
            actual_currency = self._detect_actual_currency(position.ticker, position.current_price, position.currency)
            price_owned_gbp = self._convert_to_gbp(position.average_price, position.currency, position.ticker)
            current_price_gbp = self._convert_to_gbp(position.current_price, position.currency, position.ticker)
            
            csv_data.append([
                account_type,
                position.name,
                position.ticker,
                f"{position.shares:,.4f}".rstrip('0').rstrip('.'),
                actual_currency,
                actual_currency,
                self._format_price_raw(position.average_price),
                self._format_price_raw(price_owned_gbp),
                self._format_price_raw(position.current_price),
                self._format_price_raw(current_price_gbp),
                self._format_currency_csv(position.market_value),
                self._format_profit_loss_csv(position.profit_loss),
                f"{position.profit_loss_percent.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"
            ])
        
        return csv_data
    
    def generate_summary_csv(self) -> List[List[str]]:
        """Generate CSV data for summary only."""
        csv_data = []
        
        # Add header with timestamp
        csv_data.append([f"Trading 212 Portfolio Summary - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        csv_data.append([])  # Empty row
        
        # Check if we have multiple accounts
        if len(self.clients) > 1:
            csv_data.append(["ACCOUNT SUMMARIES"])
            csv_data.append(["ACCOUNT", "FREE_FUNDS", "PORTFOLIO", "RESULT", "CURRENCY"])
            
            for account_name, summary in self.account_summaries.items():
                csv_data.append([
                    account_name,
                    self._format_currency_csv(summary.free_funds),
                    self._format_currency_csv(summary.invested),
                    self._format_profit_loss_csv(summary.result),
                    summary.currency
                ])
            
            # Combined totals if all accounts use same currency
            currencies = set(summary.currency for summary in self.account_summaries.values())
            if len(currencies) == 1:
                currency = currencies.pop()
                total_free_funds = sum(s.free_funds for s in self.account_summaries.values())
                total_invested = sum(s.invested for s in self.account_summaries.values())
                total_result = sum(s.result for s in self.account_summaries.values())
                
                csv_data.append([])
                csv_data.append(["COMBINED TOTALS"])
                csv_data.append(["TOTAL_FREE_FUNDS", "TOTAL_PORTFOLIO", "TOTAL_RESULT", "CURRENCY"])
                csv_data.append([
                    self._format_currency_csv(total_free_funds),
                    self._format_currency_csv(total_invested),
                    self._format_profit_loss_csv(total_result),
                    currency
                ])
        else:
            # Single account view
            account_name = list(self.account_summaries.keys())[0]
            if account_name in self.account_summaries:
                summary = self.account_summaries[account_name]
                csv_data.append(["SUMMARY"])
                csv_data.append(["FREE_FUNDS", "PORTFOLIO", "RESULT", "CURRENCY"])
                csv_data.append([
                    self._format_currency_csv(summary.free_funds),
                    self._format_currency_csv(summary.invested),
                    self._format_profit_loss_csv(summary.result),
                    summary.currency
                ])
        
        return csv_data
    
    def save_to_file(self, filename: str = "portfolio.md"):
        """Save the markdown output to a file."""
        markdown_content = self.generate_markdown()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\nPortfolio exported successfully to {filename}")
    
    def save_to_csv(self, positions_filename: str = "output/portfolio_positions.csv", summary_filename: str = "output/portfolio_summary.csv"):
        """Save the CSV output to separate files for positions and summary."""
        import os
        
        # Ensure output directory exists
        for filename in [positions_filename, summary_filename]:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save positions CSV
        positions_data = self.generate_positions_csv()
        with open(positions_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(positions_data)
        
        # Save summary CSV
        summary_data = self.generate_summary_csv()
        with open(summary_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(summary_data)
        
        print(f"Portfolio exported successfully to {positions_filename} and {summary_filename}")
    
    def compare_with_source_of_truth(self, source_of_truth_path: str = "source_of_truth/source_of_truth.gbp.csv") -> Dict:
        """Compare generated portfolio with source of truth data and return discrepancies."""
        import os
        
        if not os.path.exists(source_of_truth_path):
            print(f"Warning: Source of truth file not found at {source_of_truth_path}")
            return {"error": "Source of truth file not found"}
        
        # Read source of truth data
        source_data = {}
        try:
            with open(source_of_truth_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticker = row.get('Ticker', '')
                    if ticker:
                        source_data[ticker] = row
        except Exception as e:
            return {"error": f"Failed to read source of truth: {e}"}
        
        # Generate our data for comparison
        our_data = {}
        for position in self.positions:
            our_data[position.ticker] = position
        
        discrepancies = {
            "missing_in_our_data": [],
            "missing_in_source": [],
            "price_differences": [],
            "quantity_differences": [],
            "value_differences": [],
            "summary": {}
        }
        
        # Find missing positions
        source_tickers = set(source_data.keys())
        our_tickers = set(our_data.keys())
        
        discrepancies["missing_in_our_data"] = list(source_tickers - our_tickers)
        discrepancies["missing_in_source"] = list(our_tickers - source_tickers)
        
        # Compare matching positions
        common_tickers = source_tickers & our_tickers
        tolerance = Decimal('0.01')  # 1 cent tolerance
        
        for ticker in common_tickers:
            source_pos = source_data[ticker]
            our_pos = our_data[ticker]
            
            # Compare current prices
            try:
                source_current_price = Decimal(str(source_pos.get('Current Price (GBP)', '0')))
                our_current_price_gbp = self._convert_to_gbp(our_pos.current_price, our_pos.currency)
                
                if abs(source_current_price - our_current_price_gbp) > tolerance:
                    discrepancies["price_differences"].append({
                        "ticker": ticker,
                        "name": our_pos.name,
                        "source_price": float(source_current_price),
                        "our_price": float(our_current_price_gbp),
                        "difference": float(source_current_price - our_current_price_gbp)
                    })
            except (ValueError, TypeError) as e:
                print(f"Error comparing price for {ticker}: {e}")
            
            # Compare quantities
            try:
                source_quantity = Decimal(str(source_pos.get('Quantity of Shares', '0')))
                our_quantity = our_pos.shares
                
                if abs(source_quantity - our_quantity) > Decimal('0.0001'):  # Small tolerance for rounding
                    discrepancies["quantity_differences"].append({
                        "ticker": ticker,
                        "name": our_pos.name,
                        "source_quantity": float(source_quantity),
                        "our_quantity": float(our_quantity),
                        "difference": float(source_quantity - our_quantity)
                    })
            except (ValueError, TypeError) as e:
                print(f"Error comparing quantity for {ticker}: {e}")
        
        # Generate summary
        discrepancies["summary"] = {
            "total_source_positions": len(source_tickers),
            "total_our_positions": len(our_tickers),
            "common_positions": len(common_tickers),
            "missing_positions": len(discrepancies["missing_in_our_data"]) + len(discrepancies["missing_in_source"]),
            "price_discrepancies": len(discrepancies["price_differences"]),
            "quantity_discrepancies": len(discrepancies["quantity_differences"])
        }
        
        return discrepancies
    
    def generate_discrepancy_report(self, discrepancies: Dict, output_path: str = "output/discrepancy_report.md"):
        """Generate a markdown report of discrepancies."""
        import os
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        lines = []
        lines.append(f"# Portfolio Discrepancy Report")
        lines.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        if "error" in discrepancies:
            lines.append(f"## Error\n\n{discrepancies['error']}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            return
        
        # Summary
        summary = discrepancies["summary"]
        lines.append("## Summary\n")
        lines.append(f"- **Source of Truth Positions**: {summary['total_source_positions']}")
        lines.append(f"- **Our Positions**: {summary['total_our_positions']}")
        lines.append(f"- **Common Positions**: {summary['common_positions']}")
        lines.append(f"- **Missing Positions**: {summary['missing_positions']}")
        lines.append(f"- **Price Discrepancies**: {summary['price_discrepancies']}")
        lines.append(f"- **Quantity Discrepancies**: {summary['quantity_discrepancies']}")
        lines.append("")
        
        # Missing positions
        if discrepancies["missing_in_our_data"]:
            lines.append("## Positions Missing in Our Data\n")
            for ticker in discrepancies["missing_in_our_data"]:
                lines.append(f"- {ticker}")
            lines.append("")
        
        if discrepancies["missing_in_source"]:
            lines.append("## Positions Missing in Source of Truth\n")
            for ticker in discrepancies["missing_in_source"]:
                lines.append(f"- {ticker}")
            lines.append("")
        
        # Price differences
        if discrepancies["price_differences"]:
            lines.append("## Price Discrepancies\n")
            lines.append("| Ticker | Name | Source Price (GBP) | Our Price (GBP) | Difference |")
            lines.append("|--------|------|-------------------|-----------------|------------|")
            
            for diff in discrepancies["price_differences"]:
                lines.append(f"| {diff['ticker']} | {diff['name']} | {diff['source_price']:.2f} | {diff['our_price']:.2f} | {diff['difference']:+.2f} |")
            lines.append("")
        
        # Quantity differences
        if discrepancies["quantity_differences"]:
            lines.append("## Quantity Discrepancies\n")
            lines.append("| Ticker | Name | Source Quantity | Our Quantity | Difference |")
            lines.append("|--------|------|-----------------|--------------|------------|")
            
            for diff in discrepancies["quantity_differences"]:
                lines.append(f"| {diff['ticker']} | {diff['name']} | {diff['source_quantity']:.4f} | {diff['our_quantity']:.4f} | {diff['difference']:+.4f} |")
            lines.append("")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"Discrepancy report saved to {output_path}")
        return output_path
    
    def export_with_comparison(self, source_of_truth_path: str = "source_of_truth/source_of_truth.gbp.csv"):
        """Export CSV and generate discrepancy report in one step."""
        # Export CSV files
        self.save_to_csv()
        
        # Compare with source of truth and generate report
        discrepancies = self.compare_with_source_of_truth(source_of_truth_path)
        report_path = self.generate_discrepancy_report(discrepancies)
        
        return {
            "csv_exported": True,
            "discrepancy_report": report_path,
            "discrepancies": discrepancies
        }