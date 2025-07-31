"""
Data models for Trading 212 portfolio data.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Position:
    """Represents a single position in the portfolio."""
    ticker: str
    name: str
    shares: Decimal
    average_price: Decimal
    current_price: Decimal
    currency: str
    
    @property
    def market_value(self) -> Decimal:
        """Calculate current market value of the position."""
        return self.shares * self.current_price
    
    @property
    def cost_basis(self) -> Decimal:
        """Calculate total cost basis of the position."""
        return self.shares * self.average_price
    
    @property
    def profit_loss(self) -> Decimal:
        """Calculate profit/loss in currency."""
        return self.market_value - self.cost_basis
    
    @property
    def profit_loss_percent(self) -> Decimal:
        """Calculate profit/loss percentage."""
        if self.cost_basis == 0:
            return Decimal('0')
        return ((self.market_value - self.cost_basis) / self.cost_basis) * 100


@dataclass
class AccountSummary:
    """Represents account summary information."""
    free_funds: Decimal
    invested: Decimal
    result: Decimal
    currency: str = "GBP"