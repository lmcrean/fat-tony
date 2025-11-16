"""
Data models for Trading 212 portfolio data.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    """Represents a single position in the portfolio."""
    ticker: str
    name: str
    shares: Decimal
    average_price: Decimal
    current_price: Decimal
    currency: str
    account_name: str = "Trading 212"
    
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
    account_name: str = "Trading 212"


@dataclass
class OrderHistory:
    """Represents a historical order (buy or sell)."""
    order_id: int
    creation_time: datetime
    ticker: str
    name: str
    quantity: Decimal
    price: Decimal
    total_value: Decimal
    order_type: str  # e.g., "MARKET", "LIMIT", "STOP"
    status: str
    account_type: str  # e.g., "ISA", "INVEST"

    # Optional fields for performance tracking (buy orders only)
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order (positive quantity)."""
        return self.quantity > 0

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order (negative quantity)."""
        return self.quantity < 0

    @property
    def performance(self) -> Optional[Decimal]:
        """Calculate performance for buy orders if current price is available."""
        if not self.is_buy or self.current_price is None:
            return None
        return self.current_value - self.total_value if self.current_value else None

    @property
    def performance_percent(self) -> Optional[Decimal]:
        """Calculate performance percentage for buy orders."""
        if not self.is_buy or self.current_price is None or self.total_value == 0:
            return None
        perf = self.performance
        if perf is None:
            return None
        return (perf / self.total_value) * 100