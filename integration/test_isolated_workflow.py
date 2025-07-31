"""
Isolated integration tests for complete workflow scenarios.

These tests use strict isolation and validation to prevent hallucination issues.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from trading212_exporter import Trading212Client, PortfolioExporter
from .isolated_base import IsolatedIntegrationTestBase, IsolatedTestData
from .isolated_test_data import SingleAccountTestData, MultiAccountTestData, EdgeCaseTestData


@pytest.mark.integration
class TestIsolatedSingleAccountWorkflow(IsolatedIntegrationTestBase):
    """Isolated tests for single account workflow scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create isolated test data for single USD account."""
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for this test class."""
        return "Trading 212"
    
    def test_isolated_fetch_data_single_account(self):
        """Test fetching data with strict isolation and validation."""
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        # Execute fetch
        exporter.fetch_data()
        
        # Strict validation of account summaries
        assert len(exporter.account_summaries) == 1, "Should have exactly one account summary"
        assert "Trading 212" in exporter.account_summaries, "Should have Trading 212 account"
        
        account_summary = exporter.account_summaries["Trading 212"]
        self.validate_account_summary_structure(account_summary)
        
        # Exact value assertions
        assert account_summary.free_funds == test_data.expected_calculations["free_funds"], \
            f"free_funds mismatch: expected {test_data.expected_calculations['free_funds']}, got {account_summary.free_funds}"
        assert account_summary.currency == test_data.expected_calculations["account_currency"], \
            f"currency mismatch: expected {test_data.expected_calculations['account_currency']}, got {account_summary.currency}"
        assert account_summary.invested == test_data.expected_calculations["total_market_value"], \
            f"invested mismatch: expected {test_data.expected_calculations['total_market_value']}, got {account_summary.invested}"
        assert account_summary.result == test_data.expected_calculations["total_profit_loss"], \
            f"result mismatch: expected {test_data.expected_calculations['total_profit_loss']}, got {account_summary.result}"
        
        # Strict validation of positions
        assert len(exporter.positions) == test_data.expected_calculations["total_positions"], \
            f"position count mismatch: expected {test_data.expected_calculations['total_positions']}, got {len(exporter.positions)}"
        
        # Validate each position structure and calculations
        for position in exporter.positions:
            self.validate_position_structure(position)
            
            # Find corresponding test data
            position_data = next(p for p in test_data.portfolio_positions if p["ticker"] == position.ticker)
            self.assert_exact_calculation_match(position, position_data)
    
    def test_isolated_generate_markdown_single_account(self):
        """Test markdown generation with strict validation."""
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        # Fetch data first
        exporter.fetch_data()
        
        # Generate markdown
        markdown = exporter.generate_markdown()
        
        # Strict structure validation
        self.validate_markdown_structure(markdown)
        
        # Exact content validation
        for position_data in test_data.portfolio_positions:
            ticker = position_data["ticker"]
            position_name = test_data.position_details[ticker]["name"]
            
            assert position_name in markdown, f"Position name {position_name} not found in markdown"
            # Note: Ticker might not appear directly in markdown as company names are used
        
        # Validate currency formatting
        assert "USD" in markdown, "USD currency should be present in markdown"
        
        # Validate profit/loss indicators are present
        indicators = ["🟢", "🔴", "⚪"]
        has_indicators = any(indicator in markdown for indicator in indicators)
        assert has_indicators, "Profit/loss indicators should be present in markdown"
        
        # Validate summary values are present (as strings)
        free_funds_str = f"{test_data.expected_calculations['free_funds']}"
        assert free_funds_str in markdown, f"Free funds value {free_funds_str} not found in markdown"
    
    def test_isolated_save_to_file_single_account(self, tmp_path):
        """Test saving to file with strict validation."""
        exporter = self.get_exporter()  
        test_data = self.get_test_data()
        
        # Complete workflow
        exporter.fetch_data()
        generated_markdown = exporter.generate_markdown()
        
        # Save to file
        output_file = tmp_path / "isolated_single_account.md"
        exporter.save_to_file(str(output_file))
        
        # Strict file validation
        assert output_file.exists(), "Output file should exist"
        
        file_content = output_file.read_text(encoding='utf-8')
        assert file_content == generated_markdown, "File content should exactly match generated markdown"
        
        # Validate file contains expected data
        for position_data in test_data.portfolio_positions:
            ticker = position_data["ticker"]
            position_name = test_data.position_details[ticker]["name"]
            assert position_name in file_content, f"Position name {position_name} should be in saved file"
    
    def test_isolated_complete_workflow_validation(self, tmp_path):
        """Test complete workflow with comprehensive validation."""
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        # Step 1: Fetch and validate data
        exporter.fetch_data()
        
        # Validate state after fetch
        assert len(exporter.positions) == 3, "Should have exactly 3 positions"
        assert len(exporter.account_summaries) == 1, "Should have exactly 1 account summary"
        
        # Calculate and verify totals
        total_market_value = sum(p.market_value for p in exporter.positions)
        total_profit_loss = sum(p.profit_loss for p in exporter.positions)
        
        assert total_market_value == test_data.expected_calculations["total_market_value"], \
            f"Total market value mismatch: expected {test_data.expected_calculations['total_market_value']}, got {total_market_value}"
        assert total_profit_loss == test_data.expected_calculations["total_profit_loss"], \
            f"Total profit/loss mismatch: expected {test_data.expected_calculations['total_profit_loss']}, got {total_profit_loss}"
        
        # Step 2: Generate and validate markdown
        markdown = exporter.generate_markdown()
        self.validate_markdown_structure(markdown)
        
        # Step 3: Save and validate file
        output_file = tmp_path / "isolated_complete_workflow.md"
        exporter.save_to_file(str(output_file))
        
        assert output_file.exists(), "Output file should exist"
        file_content = output_file.read_text(encoding='utf-8')
        assert len(file_content) > 500, "File should contain substantial content"  # Adjusted expectation
        assert file_content == markdown, "File content should match generated markdown"


@pytest.mark.integration 
class TestIsolatedMultiAccountWorkflow(IsolatedIntegrationTestBase):
    """Isolated tests for multi-account workflow scenarios."""
    
    def setup_method(self):
        """Set up multi-account test environment."""
        # Override base setup for multi-account scenario
        self._test_data_dict = MultiAccountTestData.create_isa_and_invest_accounts()
        self._mock_clients = self._create_isolated_multi_account_clients()
        self._exporter = PortfolioExporter(self._mock_clients)
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Not used for multi-account tests."""
        pass
    
    def get_account_name(self) -> str:
        """Not used for multi-account tests."""  
        pass
    
    def _create_isolated_multi_account_clients(self) -> dict:
        """Create isolated mock clients for multi-account testing."""
        clients = {}
        
        for account_name, test_data in self._test_data_dict.items():
            client = Mock(spec=Trading212Client)
            client.account_name = account_name
            client._request_interval = 5
            
            # Configure with isolated test data
            isolated_data = test_data.copy()
            client.get_account_metadata.return_value = isolated_data.account_metadata
            client.get_account_cash.return_value = isolated_data.account_cash
            client.get_portfolio.return_value = isolated_data.portfolio_positions
            
            def create_position_details_handler(data):
                def handler(ticker: str):
                    if ticker in data.position_details:
                        return data.position_details[ticker].copy()
                    return {"ticker": ticker, "name": ticker}
                return handler
            
            client.get_position_details.side_effect = create_position_details_handler(isolated_data)
            clients[account_name] = client
        
        return clients
    
    def test_isolated_fetch_data_multi_account(self):
        """Test multi-account data fetching with strict validation."""
        self._exporter.fetch_data()
        
        # Validate account summaries
        assert len(self._exporter.account_summaries) == 2, "Should have exactly 2 account summaries"
        assert "Stocks & Shares ISA" in self._exporter.account_summaries, "Should have ISA account"
        assert "Invest Account" in self._exporter.account_summaries, "Should have Invest account"
        
        # Validate ISA account
        isa_summary = self._exporter.account_summaries["Stocks & Shares ISA"]
        isa_test_data = self._test_data_dict["Stocks & Shares ISA"]
        
        assert isa_summary.account_name == "Stocks & Shares ISA", "ISA account name mismatch"
        assert isa_summary.currency == "GBP", "ISA currency should be GBP"
        assert isa_summary.free_funds == isa_test_data.expected_calculations["free_funds"], "ISA free funds mismatch"
        assert isa_summary.invested == isa_test_data.expected_calculations["total_market_value"], "ISA invested mismatch"
        assert isa_summary.result == isa_test_data.expected_calculations["total_profit_loss"], "ISA result mismatch"
        
        # Validate Invest account
        invest_summary = self._exporter.account_summaries["Invest Account"]
        invest_test_data = self._test_data_dict["Invest Account"]
        
        assert invest_summary.account_name == "Invest Account", "Invest account name mismatch"
        assert invest_summary.currency == "USD", "Invest currency should be USD"
        assert invest_summary.free_funds == invest_test_data.expected_calculations["free_funds"], "Invest free funds mismatch"
        assert invest_summary.invested == invest_test_data.expected_calculations["total_market_value"], "Invest invested mismatch"
        assert invest_summary.result == invest_test_data.expected_calculations["total_profit_loss"], "Invest result mismatch"
        
        # Validate positions
        expected_total_positions = sum(data.expected_calculations["total_positions"] for data in self._test_data_dict.values())
        assert len(self._exporter.positions) == expected_total_positions, f"Should have {expected_total_positions} total positions"
        
        # Validate position account attribution
        isa_positions = [p for p in self._exporter.positions if p.account_name == "Stocks & Shares ISA"]
        invest_positions = [p for p in self._exporter.positions if p.account_name == "Invest Account"]
        
        assert len(isa_positions) == 2, "Should have 2 ISA positions"
        assert len(invest_positions) == 1, "Should have 1 Invest position"
        
        # Validate ISA positions
        for position in isa_positions:
            assert position.currency == "GBP", f"ISA position {position.ticker} should be GBP"
            assert position.ticker in ["VOD.L", "LLOY.L"], f"ISA position ticker {position.ticker} unexpected"
        
        # Validate Invest positions  
        for position in invest_positions:
            assert position.currency == "USD", f"Invest position {position.ticker} should be USD"
            assert position.ticker == "AAPL", f"Invest position ticker {position.ticker} unexpected"
    
    def test_isolated_generate_markdown_multi_account(self):
        """Test multi-account markdown generation with strict validation."""
        self._exporter.fetch_data()
        markdown = self._exporter.generate_markdown()
        
        # Validate multi-account structure
        assert "# Trading 212 Portfolio" in markdown, "Should have main title"
        assert "## Stocks & Shares ISA" in markdown, "Should have ISA section"
        assert "## Invest Account" in markdown, "Should have Invest section"
        
        # Validate account-specific content
        assert "Vodafone Group Plc" in markdown, "Should contain ISA position"
        assert "Lloyds Banking Group Plc" in markdown, "Should contain ISA position"
        assert "Apple Inc." in markdown, "Should contain Invest position"
        
        # Validate currency formatting
        assert "GBP" in markdown or "£" in markdown, "Should contain GBP currency"
        assert "USD" in markdown, "Should contain USD currency"
        
        # Validate no combined totals (different currencies)
        assert "## Combined Totals" not in markdown, "Should not have combined totals with different currencies"
        assert "TOTAL FREE FUNDS" not in markdown, "Should not have total free funds with different currencies"
    
    def test_isolated_save_multi_account_file(self, tmp_path):
        """Test multi-account file saving with strict validation."""
        self._exporter.fetch_data()
        markdown = self._exporter.generate_markdown()
        
        output_file = tmp_path / "isolated_multi_account.md"
        self._exporter.save_to_file(str(output_file))
        
        assert output_file.exists(), "Output file should exist"
        file_content = output_file.read_text(encoding='utf-8')
        assert file_content == markdown, "File content should match generated markdown"
        
        # Validate multi-account specific content in file
        assert "Stocks & Shares ISA" in file_content, "File should contain ISA section"
        assert "Invest Account" in file_content, "File should contain Invest section"


@pytest.mark.integration
class TestIsolatedEdgeCaseWorkflows(IsolatedIntegrationTestBase):
    """Isolated tests for edge case workflow scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create empty portfolio test data."""
        return EdgeCaseTestData.create_empty_portfolio()
    
    def get_account_name(self) -> str:
        """Get account name for edge case tests."""
        return "Trading 212"
    
    def test_isolated_empty_portfolio_workflow(self):
        """Test empty portfolio workflow with strict validation."""
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        # Fetch data
        exporter.fetch_data()
        
        # Validate empty portfolio state
        assert len(exporter.positions) == 0, "Empty portfolio should have no positions"
        assert len(exporter.account_summaries) == 1, "Should have one account summary"
        
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.free_funds == Decimal("0.0"), "Empty portfolio should have zero free funds"
        assert account_summary.invested == Decimal("0.0"), "Empty portfolio should have zero invested"
        assert account_summary.result == Decimal("0.0"), "Empty portfolio should have zero result"
        
        # Generate markdown
        markdown = exporter.generate_markdown()
        assert isinstance(markdown, str), "Should generate valid markdown"
        assert "# Trading 212 Portfolio" in markdown, "Should have title"
        assert "## Summary" in markdown, "Should have summary section"
        
        # Should not have positions section for empty portfolio
        if len(exporter.positions) == 0:
            # Markdown structure should adapt to empty portfolio
            assert "FREE FUNDS" in markdown, "Should show free funds"
            assert "PORTFOLIO" in markdown, "Should show portfolio total"
    
    def test_isolated_fractional_shares_workflow(self, tmp_path):
        """Test fractional shares workflow with strict validation."""
        # Override test data for fractional shares
        self._test_data = EdgeCaseTestData.create_fractional_shares()
        self._mock_client = self._create_isolated_mock_client()
        self._exporter = PortfolioExporter({"Trading 212": self._mock_client})
        
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        # Fetch data
        exporter.fetch_data()
        
        # Validate fractional share handling
        assert len(exporter.positions) == 2, "Should have 2 fractional positions"
        
        # Check specific fractional values
        amzn_position = next(p for p in exporter.positions if p.ticker == "AMZN")
        assert amzn_position.shares == Decimal("0.5"), "AMZN shares should be 0.5"
        
        brk_position = next(p for p in exporter.positions if p.ticker == "BRK.A")
        assert brk_position.shares == Decimal("0.001"), "BRK.A shares should be 0.001"
        
        # Generate and validate markdown
        markdown = exporter.generate_markdown()
        assert "0.5" in markdown, "Should show AMZN fractional shares"
        assert "0.001" in markdown, "Should show BRK.A fractional shares"
        
        # Save and validate file
        output_file = tmp_path / "isolated_fractional.md"
        exporter.save_to_file(str(output_file))
        
        file_content = output_file.read_text(encoding='utf-8')
        assert "0.5" in file_content, "File should contain fractional shares"
        assert "Amazon.com Inc." in file_content, "File should contain Amazon name"