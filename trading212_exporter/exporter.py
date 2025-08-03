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
    
    def _is_uk_etf_priced_in_pence(self, ticker: str, current_price: Decimal) -> bool:
        """
        Determine if a UK ETF is priced in pence (GBX) instead of pounds (GBP).
        
        Based on analysis of Trading 212 API data, certain UK ETFs return prices in pence
        while others return prices in pounds. This function identifies which need conversion.
        """
        # Specific tickers confirmed to be priced in pence (from source of truth analysis)
        known_pence_tickers = {
            'IITU_EQ',   # iShares S&P 500 IT - price ~2827 should be ~£28.27
            'INTLl_EQ',  # WisdomTree AI - price ~5557 should be ~£55.57
            'SGLNl_EQ',  # iShares Physical Gold - price ~4910 should be ~£49.10
            'CNX1_EQ',   # iShares NASDAQ 100 - price ~98520 should be ~£985.20
            'VUAGl_EQ',  # Vanguard S&P 500 (Acc) - price ~8998 should be ~£89.98
            'VGERl_EQ',  # Vanguard Germany All Cap - price ~2943 should be ~£29.43
            'SMGBl_EQ',  # VanEck Semiconductor (Acc) - price ~3553 should be ~£35.53
            'VWRPl_EQ',  # Vanguard FTSE All-World (Acc) - price ~11508 should be ~£115.08
            'RBODl_EQ',  # iShares Automation & Robotics (Dist) - price ~995 should be ~£9.95
            'IINDl_EQ',  # iShares MSCI India (Acc) - price ~713 should be ~£7.13
            'FXACa_EQ',  # iShares China Large Cap (Acc) - price ~415 should be ~£4.15
            'EXICd_EQ',  # iShares Core DAX DE (Dist) - price ~684 should be ~£6.84
        }
        
        # US stocks should never be converted (they have _US_EQ suffix)
        is_us_stock = '_US_EQ' in ticker
        
        # Only convert specific known pence tickers that are not US stocks
        should_convert = not is_us_stock and ticker in known_pence_tickers
        
        if should_convert:
            print(f"    Detected pence pricing for {ticker}: {current_price} -> {current_price/100}")
        
        return should_convert
    
    def _convert_pence_to_pounds(self, value: Decimal) -> Decimal:
        """Convert a price from pence to pounds by dividing by 100."""
        return value / Decimal('100')
    
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
                
                # Get raw price data
                raw_avg_price = Decimal(str(position_data['averagePrice']))
                raw_current_price = Decimal(str(position_data['currentPrice']))
                
                # Check if this UK ETF is priced in pence and needs conversion
                if self._is_uk_etf_priced_in_pence(ticker, raw_current_price):
                    avg_price = self._convert_pence_to_pounds(raw_avg_price)
                    current_price = self._convert_pence_to_pounds(raw_current_price)
                else:
                    avg_price = raw_avg_price
                    current_price = raw_current_price
                
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
        """Generate CSV data for positions only."""
        csv_data = []
        
        # Add header with timestamp
        csv_data.append([f"Trading 212 Portfolio Positions - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        csv_data.append([])  # Empty row
        
        # Check if we have multiple accounts
        if len(self.clients) > 1:
            # Multi-account view: include account column
            csv_data.append(["ACCOUNT", "NAME", "SHARES", "AVERAGE_PRICE", "CURRENT_PRICE", "MARKET_VALUE", "RESULT", "RESULT_%", "CURRENCY"])
            
            for account_name in self.clients.keys():
                account_positions = [p for p in self.positions if p.account_name == account_name]
                
                for position in sorted(account_positions, key=lambda p: p.market_value, reverse=True):
                    csv_data.append([
                        account_name,
                        position.name,
                        f"{position.shares:,.4f}".rstrip('0').rstrip('.'),
                        self._format_currency_csv(position.average_price),
                        self._format_currency_csv(position.current_price),
                        self._format_currency_csv(position.market_value),
                        self._format_profit_loss_csv(position.profit_loss),
                        self._format_percentage_csv(position.profit_loss_percent),
                        position.currency
                    ])
        else:
            # Single account view
            csv_data.append(["NAME", "SHARES", "AVERAGE_PRICE", "CURRENT_PRICE", "MARKET_VALUE", "RESULT", "RESULT_%", "CURRENCY"])
            
            for position in sorted(self.positions, key=lambda p: p.market_value, reverse=True):
                csv_data.append([
                    position.name,
                    f"{position.shares:,.4f}".rstrip('0').rstrip('.'),
                    self._format_currency_csv(position.average_price),
                    self._format_currency_csv(position.current_price),
                    self._format_currency_csv(position.market_value),
                    self._format_profit_loss_csv(position.profit_loss),
                    self._format_percentage_csv(position.profit_loss_percent),
                    position.currency
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
    
    def save_to_csv(self, positions_filename: str = "portfolio_positions.csv", summary_filename: str = "portfolio_summary.csv"):
        """Save the CSV output to separate files for positions and summary."""
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