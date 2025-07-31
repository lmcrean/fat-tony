"""
Portfolio data processing and markdown generation.
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from tabulate import tabulate

from .models import Position, AccountSummary
from .client import Trading212Client


class PortfolioExporter:
    """Handles portfolio data processing and markdown generation."""
    
    def __init__(self, client: Trading212Client):
        """Initialize the exporter with a Trading 212 client."""
        self.client = client
        self.positions: List[Position] = []
        self.account_summary: Optional[AccountSummary] = None
    
    def fetch_data(self):
        """Fetch all necessary data from the API."""
        print("Fetching portfolio data...")
        
        # Get account metadata for currency (optional - may fail due to API permissions)
        try:
            metadata = self.client.get_account_metadata()
            account_currency = metadata.get('currencyCode', 'GBP')
            print(f"Account currency: {account_currency}")
        except Exception as e:
            print(f"Could not fetch account metadata (API permissions): {e}")
            account_currency = 'GBP'  # Default currency when account access is restricted
        
        # Get portfolio positions
        portfolio_data = self.client.get_portfolio()
        
        # Process each position
        for position_data in portfolio_data:
            ticker = position_data['ticker']
            
            # Get detailed position info
            print(f"Fetching details for {ticker}...")
            try:
                details = self.client.get_position_details(ticker)
                
                position = Position(
                    ticker=ticker,
                    name=details.get('name', ticker),
                    shares=Decimal(str(position_data['quantity'])),
                    average_price=Decimal(str(position_data['averagePrice'])),
                    current_price=Decimal(str(position_data['currentPrice'])),
                    currency=position_data.get('currencyCode', account_currency)
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
                    currency=position_data.get('currencyCode', account_currency)
                )
                self.positions.append(position)
        
        # Get cash balance (optional - may fail due to API permissions)
        print("Fetching cash balance...")
        try:
            cash_data = self.client.get_account_cash()
            free_funds = Decimal(str(cash_data.get('free', 0)))
        except Exception as e:
            print(f"Could not fetch cash balance (API permissions): {e}")
            free_funds = Decimal('0')  # Default when account access is restricted
        
        # Calculate summary
        total_invested = sum(p.cost_basis for p in self.positions)
        total_value = sum(p.market_value for p in self.positions)
        total_result = total_value - total_invested
        
        self.account_summary = AccountSummary(
            free_funds=free_funds,
            invested=total_value,
            result=total_result,
            currency=account_currency
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
        if self.account_summary:
            lines.append("\n## Summary\n")
            summary_data = [
                ["FREE FUNDS", self._format_currency(self.account_summary.free_funds)],
                ["PORTFOLIO", self._format_currency(self.account_summary.invested)],
                ["RESULT", self._format_profit_loss(self.account_summary.result)]
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