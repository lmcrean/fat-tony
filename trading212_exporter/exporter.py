"""
Portfolio data processing and markdown generation.
"""

from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from tabulate import tabulate

from .models import Position, AccountSummary
from .client import Trading212Client


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
            
            # Process each position
            for position_data in portfolio_data:
                ticker = position_data['ticker']
                
                # Get detailed position info
                print(f"Fetching details for {ticker}...")
                try:
                    details = client.get_position_details(ticker)
                    
                    position = Position(
                        ticker=ticker,
                        name=details.get('name', ticker),
                        shares=Decimal(str(position_data['quantity'])),
                        average_price=Decimal(str(position_data['averagePrice'])),
                        current_price=Decimal(str(position_data['currentPrice'])),
                        currency=position_data.get('currencyCode', account_currency),
                        account_name=account_name
                    )
                    self.positions.append(position)
                except Exception as e:
                    print(f"Error fetching details for {ticker}: {e}")
                    # Use basic data if detailed fetch fails
                    position = Position(
                        ticker=ticker,
                        name=ticker,
                        shares=Decimal(str(position_data['quantity'])),
                        average_price=Decimal(str(position_data['averagePrice'])),
                        current_price=Decimal(str(position_data['currentPrice'])),
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
                invested=total_value,
                result=total_result,
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
    
    def save_to_file(self, filename: str = "portfolio.md"):
        """Save the markdown output to a file."""
        markdown_content = self.generate_markdown()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\nPortfolio exported successfully to {filename}")