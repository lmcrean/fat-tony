"""
Isolated test data definitions for integration tests.

This module provides strictly validated test data that ensures no hallucination
issues by maintaining exact correspondence with real API responses.
"""

from decimal import Decimal
from typing import Dict, Any, List
from .isolated_base import IsolatedTestData


class SingleAccountTestData:
    """Isolated test data for single account scenarios."""
    
    @staticmethod
    def create_usd_account() -> IsolatedTestData:
        """Create isolated test data for a USD account with multiple positions."""
        return IsolatedTestData(
            account_metadata={
                "currencyCode": "USD",
                "id": 12345,
                "type": "LIVE"
            },
            account_cash={
                "free": 850.75,
                "total": 850.75,
                "result": 0.0,
                "interest": 0.0
            },
            portfolio_positions=[
                {
                    "ticker": "AAPL",
                    "quantity": 10.0,
                    "averagePrice": 150.0,
                    "currentPrice": 160.0,
                    "currencyCode": "USD"
                },
                {
                    "ticker": "GOOGL", 
                    "quantity": 5.0,
                    "averagePrice": 2000.0,
                    "currentPrice": 1900.0,
                    "currencyCode": "USD"
                },
                {
                    "ticker": "TSLA",
                    "quantity": 25.0,
                    "averagePrice": 200.0,
                    "currentPrice": 220.0,
                    "currencyCode": "USD"
                }
            ],
            position_details={
                "AAPL": {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "type": "STOCK",
                    "currencyCode": "USD"
                },
                "GOOGL": {
                    "ticker": "GOOGL", 
                    "name": "Alphabet Inc.",
                    "type": "STOCK",
                    "currencyCode": "USD"
                },
                "TSLA": {
                    "ticker": "TSLA",
                    "name": "Tesla Inc.",
                    "type": "STOCK",
                    "currencyCode": "USD"
                }
            },
            expected_calculations={
                "total_positions": 3,
                "total_market_value": Decimal("16600.0"),  # 1600 + 9500 + 5500
                "total_cost_basis": Decimal("16500.0"),    # 1500 + 10000 + 5000
                "total_profit_loss": Decimal("100.0"),     # 100 + (-500) + 500
                "account_currency": "USD",
                "free_funds": Decimal("850.75")
            }
        )
    
    @staticmethod
    def create_gbp_account() -> IsolatedTestData:
        """Create isolated test data for a GBP account with UK stocks."""
        return IsolatedTestData(
            account_metadata={
                "currencyCode": "GBP",
                "id": 67890,
                "type": "ISA"
            },
            account_cash={
                "free": 500.25,
                "total": 500.25,
                "result": 0.0,
                "interest": 0.0
            },
            portfolio_positions=[
                {
                    "ticker": "VOD.L",
                    "quantity": 100.0,
                    "averagePrice": 1.25,
                    "currentPrice": 1.30,
                    "currencyCode": "GBP"
                },
                {
                    "ticker": "LLOY.L",
                    "quantity": 500.0,
                    "averagePrice": 0.45,
                    "currentPrice": 0.50,
                    "currencyCode": "GBP"
                }
            ],
            position_details={
                "VOD.L": {
                    "ticker": "VOD.L",
                    "name": "Vodafone Group Plc",
                    "type": "STOCK",
                    "currencyCode": "GBP"
                },
                "LLOY.L": {
                    "ticker": "LLOY.L",
                    "name": "Lloyds Banking Group Plc",
                    "type": "STOCK", 
                    "currencyCode": "GBP"
                }
            },
            expected_calculations={
                "total_positions": 2,
                "total_market_value": Decimal("380.0"),   # 130 + 250
                "total_cost_basis": Decimal("350.0"),     # 125 + 225
                "total_profit_loss": Decimal("30.0"),     # 5 + 25
                "account_currency": "GBP",
                "free_funds": Decimal("500.25")
            }
        )


class MultiAccountTestData:
    """Isolated test data for multi-account scenarios."""
    
    @staticmethod
    def create_isa_and_invest_accounts() -> Dict[str, IsolatedTestData]:
        """Create isolated test data for ISA and Invest accounts."""
        return {
            "Stocks & Shares ISA": IsolatedTestData(
                account_metadata={
                    "currencyCode": "GBP",
                    "id": 11111,
                    "type": "ISA"
                },
                account_cash={
                    "free": 500.25,
                    "total": 500.25,
                    "result": 0.0,
                    "interest": 0.0
                },
                portfolio_positions=[
                    {
                        "ticker": "VOD.L",
                        "quantity": 100.0,
                        "averagePrice": 1.25,
                        "currentPrice": 1.30,
                        "currencyCode": "GBP"
                    },
                    {
                        "ticker": "LLOY.L",
                        "quantity": 500.0,
                        "averagePrice": 0.45,
                        "currentPrice": 0.50,
                        "currencyCode": "GBP"
                    }
                ],
                position_details={
                    "VOD.L": {
                        "ticker": "VOD.L",
                        "name": "Vodafone Group Plc",
                        "type": "STOCK",
                        "currencyCode": "GBP"
                    },
                    "LLOY.L": {
                        "ticker": "LLOY.L",
                        "name": "Lloyds Banking Group Plc",
                        "type": "STOCK",
                        "currencyCode": "GBP"
                    }
                },
                expected_calculations={
                    "total_positions": 2,
                    "total_market_value": Decimal("380.0"),
                    "total_cost_basis": Decimal("350.0"),
                    "total_profit_loss": Decimal("30.0"),
                    "account_currency": "GBP",
                    "free_funds": Decimal("500.25")
                }
            ),
            "Invest Account": IsolatedTestData(
                account_metadata={
                    "currencyCode": "USD",
                    "id": 22222,
                    "type": "LIVE"
                },
                account_cash={
                    "free": 850.75,
                    "total": 850.75,
                    "result": 0.0,
                    "interest": 0.0
                },
                portfolio_positions=[
                    {
                        "ticker": "AAPL",
                        "quantity": 10.0,
                        "averagePrice": 150.0,
                        "currentPrice": 160.0,
                        "currencyCode": "USD"
                    }
                ],
                position_details={
                    "AAPL": {
                        "ticker": "AAPL",
                        "name": "Apple Inc.",
                        "type": "STOCK",
                        "currencyCode": "USD"
                    }
                },
                expected_calculations={
                    "total_positions": 1,
                    "total_market_value": Decimal("1600.0"),
                    "total_cost_basis": Decimal("1500.0"),
                    "total_profit_loss": Decimal("100.0"),
                    "account_currency": "USD",
                    "free_funds": Decimal("850.75")
                }
            )
        }


class EdgeCaseTestData:
    """Isolated test data for edge cases and error scenarios."""
    
    @staticmethod
    def create_empty_portfolio() -> IsolatedTestData:
        """Create isolated test data for an empty portfolio."""
        return IsolatedTestData(
            account_metadata={
                "currencyCode": "USD",
                "id": 99999,
                "type": "LIVE"
            },
            account_cash={
                "free": 0.0,
                "total": 0.0,
                "result": 0.0,
                "interest": 0.0
            },
            portfolio_positions=[],
            position_details={},
            expected_calculations={
                "total_positions": 0,
                "total_market_value": Decimal("0.0"),
                "total_cost_basis": Decimal("0.0"),
                "total_profit_loss": Decimal("0.0"),
                "account_currency": "USD",
                "free_funds": Decimal("0.0")
            }
        )
    
    @staticmethod
    def create_fractional_shares() -> IsolatedTestData:
        """Create isolated test data for fractional shares."""
        return IsolatedTestData(
            account_metadata={
                "currencyCode": "USD",
                "id": 33333,
                "type": "LIVE"
            },
            account_cash={
                "free": 1000.0,
                "total": 1000.0,
                "result": 0.0,
                "interest": 0.0
            },
            portfolio_positions=[
                {
                    "ticker": "AMZN",
                    "quantity": 0.5,
                    "averagePrice": 3000.0,
                    "currentPrice": 3100.0,
                    "currencyCode": "USD"
                },
                {
                    "ticker": "BRK.A",
                    "quantity": 0.001,
                    "averagePrice": 500000.0,
                    "currentPrice": 520000.0,
                    "currencyCode": "USD"
                }
            ],
            position_details={
                "AMZN": {
                    "ticker": "AMZN",
                    "name": "Amazon.com Inc.",
                    "type": "STOCK",
                    "currencyCode": "USD"
                },
                "BRK.A": {
                    "ticker": "BRK.A",
                    "name": "Berkshire Hathaway Inc.",
                    "type": "STOCK",
                    "currencyCode": "USD"
                }
            },
            expected_calculations={
                "total_positions": 2,
                "total_market_value": Decimal("2070.0"),   # 1550 + 520
                "total_cost_basis": Decimal("2000.0"),     # 1500 + 500
                "total_profit_loss": Decimal("70.0"),      # 50 + 20
                "account_currency": "USD",
                "free_funds": Decimal("1000.0")
            }
        )
    
    @staticmethod
    def create_error_prone_scenario() -> IsolatedTestData:
        """Create isolated test data for API error scenarios."""
        return IsolatedTestData(
            account_metadata={
                "error": "API permission denied",
                "status_code": 403
            },
            account_cash={
                "error": "API permission denied", 
                "status_code": 403
            },
            portfolio_positions=[
                {
                    "ticker": "AAPL",
                    "quantity": 10.0,
                    "averagePrice": 150.0,
                    "currentPrice": 160.0,
                    "currencyCode": "USD"
                }
            ],
            position_details={
                "AAPL": {
                    "error": "API Error",
                    "status_code": 500
                }
            },
            expected_calculations={
                "total_positions": 1,
                "total_market_value": Decimal("1600.0"),
                "total_cost_basis": Decimal("1500.0"),
                "total_profit_loss": Decimal("100.0"),
                "account_currency": "USD",  # Fallback
                "free_funds": Decimal("0.0")  # Error fallback
            }
        )


class PerformanceTestData:
    """Isolated test data for performance testing scenarios."""
    
    @staticmethod
    def create_large_portfolio() -> IsolatedTestData:
        """Create isolated test data for performance testing with many positions."""
        portfolio_positions = []
        position_details = {}
        
        # Generate 50 positions for performance testing
        tickers = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "CRM", "ADBE",
            "INTC", "ORCL", "CSCO", "IBM", "AMD", "QCOM", "TXN", "AVGO", "NOW", "MU",
            "AMAT", "LRCX", "KLAC", "MCHP", "ADI", "MRVL", "XLNX", "SWKS", "QRVO", "MPWR",
            "VOD.L", "LLOY.L", "BP.L", "SHEL.L", "AZN.L", "GSK.L", "DGE.L", "ULVR.L", "RDSB.L", "BT-A.L",
            "BARC.L", "HSBA.L", "RBS.L", "LSE.L", "NG.L", "BLT.L", "RIO.L", "AAL.L", "BA.L", "GLEN.L"
        ]
        
        total_market_value = Decimal("0")
        total_cost_basis = Decimal("0")
        
        for i, ticker in enumerate(tickers):
            quantity = 10.0 + (i * 5.0)  # Varying quantities
            avg_price = 100.0 + (i * 10.0)  # Varying prices
            current_price = avg_price * (0.9 + (i * 0.004))  # Some winners, some losers
            
            is_gbp = ticker.endswith(".L")
            currency = "GBP" if is_gbp else "USD"
            
            position = {
                "ticker": ticker,
                "quantity": quantity,
                "averagePrice": avg_price,
                "currentPrice": current_price,
                "currencyCode": currency
            }
            portfolio_positions.append(position)
            
            position_details[ticker] = {
                "ticker": ticker,
                "name": f"{ticker.replace('.L', '')} Inc." if not is_gbp else f"{ticker.replace('.L', '')} Plc",
                "type": "STOCK",
                "currencyCode": currency
            }
            
            # Calculate totals for verification (convert GBP to USD for simplicity)
            conversion_rate = Decimal("1.25") if is_gbp else Decimal("1.0")
            market_val = Decimal(str(quantity * current_price)) * conversion_rate
            cost_val = Decimal(str(quantity * avg_price)) * conversion_rate
            
            total_market_value += market_val
            total_cost_basis += cost_val
        
        return IsolatedTestData(
            account_metadata={
                "currencyCode": "USD",
                "id": 44444,
                "type": "LIVE"
            },
            account_cash={
                "free": 5000.0,
                "total": 5000.0,
                "result": 0.0,
                "interest": 0.0
            },
            portfolio_positions=portfolio_positions,
            position_details=position_details,
            expected_calculations={
                "total_positions": 50,
                "total_market_value": total_market_value,
                "total_cost_basis": total_cost_basis,
                "total_profit_loss": total_market_value - total_cost_basis,
                "account_currency": "USD",
                "free_funds": Decimal("5000.0")
            }
        )