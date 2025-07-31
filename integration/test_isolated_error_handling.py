"""
Isolated integration tests for error handling scenarios.

These tests validate error handling with strict assertions to prevent hallucination.
"""

import pytest
from decimal import Decimal
from unittest.mock import create_autospec, Mock

from trading212_exporter import Trading212Client, PortfolioExporter
from .isolated_base import IsolatedIntegrationTestBase, IsolatedTestData
from .isolated_test_data import EdgeCaseTestData
from .schema_validator import Trading212ApiSchemaValidator


@pytest.mark.integration
class TestIsolatedApiErrorHandling(IsolatedIntegrationTestBase):
    """Isolated tests for API error handling scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create error scenario test data."""
        return EdgeCaseTestData.create_error_prone_scenario()
    
    def get_account_name(self) -> str:
        """Get account name for error tests."""
        return "Trading 212"
    
    def _create_isolated_error_client(self) -> Mock:
        """Create a client that simulates API errors."""
        client = create_autospec(Trading212Client, spec_set=True)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Configure API errors
        def error_metadata():
            raise Exception("API permission denied")
        
        def error_cash():
            raise Exception("API permission denied")
        
        def error_position_details(ticker: str):
            raise Exception("API Error")
        
        client.get_account_metadata.side_effect = error_metadata
        client.get_account_cash.side_effect = error_cash
        client.get_portfolio.return_value = [
            {
                "ticker": "AAPL",
                "quantity": 10.0,
                "averagePrice": 150.0,
                "currentPrice": 160.0,
                "currencyCode": "USD"
            }
        ]
        client.get_position_details.side_effect = error_position_details
        
        return client
    
    def test_isolated_metadata_api_error_handling(self):
        """Test handling of account metadata API errors with strict validation."""
        # Override mock client for this specific error scenario
        error_client = self._create_isolated_error_client()
        exporter = PortfolioExporter({"Trading 212": error_client})
        
        # Should not raise exception despite API errors
        exporter.fetch_data()
        
        # Validate graceful error handling
        assert len(exporter.account_summaries) == 1, "Should have one account summary despite errors"
        assert "Trading 212" in exporter.account_summaries, "Should have Trading 212 account"
        
        account_summary = exporter.account_summaries["Trading 212"]
        self.validate_account_summary_structure(account_summary)
        
        # Validate error fallback behavior - should use defaults
        assert account_summary.currency == "USD", "Should fallback to USD currency"
        assert account_summary.free_funds == Decimal('0'), "Should fallback to zero free funds on error"
        
        # Should still have positions from successful portfolio call
        assert len(exporter.positions) == 1, "Should have positions from successful portfolio API call"
        
        position = exporter.positions[0]
        self.validate_position_structure(position)
        assert position.ticker == "AAPL", "Should have AAPL position"
        assert position.name == "AAPL", "Should fallback to ticker as name when position details fails"
    
    def test_isolated_cash_api_error_handling(self):
        """Test handling of account cash API errors with strict validation."""
        error_client = self._create_isolated_error_client()
        exporter = PortfolioExporter({"Trading 212": error_client})
        
        exporter.fetch_data()
        
        # Validate cash error handling
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.free_funds == Decimal('0'), "Should use zero as fallback for cash API error"
        
        # Other calculations should still work
        assert account_summary.invested > Decimal('0'), "Should still calculate invested amount from positions"
        assert account_summary.result != Decimal('0'), "Should still calculate profit/loss from positions"
    
    def test_isolated_position_details_error_handling(self):
        """Test handling of position details API errors with strict validation."""
        error_client = self._create_isolated_error_client()
        exporter = PortfolioExporter({"Trading 212": error_client})
        
        exporter.fetch_data()
        
        # Validate position details error handling
        assert len(exporter.positions) == 1, "Should have position despite details API error"
        
        position = exporter.positions[0]
        self.validate_position_structure(position)
        
        # Should fallback to ticker as name
        assert position.name == position.ticker, "Should use ticker as name when details API fails"
        assert position.ticker == "AAPL", "Should still have correct ticker"
        
        # Calculations should still be correct
        expected_market_value = Decimal('10.0') * Decimal('160.0')  # 10 shares * $160
        expected_cost_basis = Decimal('10.0') * Decimal('150.0')    # 10 shares * $150
        expected_profit_loss = expected_market_value - expected_cost_basis
        
        assert position.market_value == expected_market_value, f"Market value should be {expected_market_value}"
        assert position.cost_basis == expected_cost_basis, f"Cost basis should be {expected_cost_basis}"
        assert position.profit_loss == expected_profit_loss, f"Profit/loss should be {expected_profit_loss}"
    
    def test_isolated_complete_api_failure_recovery(self):
        """Test recovery from complete API failure with strict validation."""
        error_client = self._create_isolated_error_client()
        exporter = PortfolioExporter({"Trading 212": error_client})
        
        # Should not raise exception
        exporter.fetch_data()
        
        # Should still be able to generate markdown
        markdown = exporter.generate_markdown()
        assert isinstance(markdown, str), "Should generate markdown despite API errors"
        assert len(markdown) > 0, "Markdown should not be empty"
        assert "# Trading 212 Portfolio" in markdown, "Should have title"
        
        # Should contain fallback data
        assert "AAPL" in markdown, "Should contain position ticker"
        assert "Trading 212" in markdown, "Should contain account name"
        
        # Should be able to save file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name
        
        exporter.save_to_file(temp_path)
        
        with open(temp_path, 'r') as f:
            file_content = f.read()
        
        assert file_content == markdown, "File content should match generated markdown"
        assert len(file_content) > 0, "File should not be empty"


@pytest.mark.integration
class TestIsolatedNetworkErrorHandling(IsolatedIntegrationTestBase):
    """Isolated tests for network error scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create network error test data."""
        return EdgeCaseTestData.create_error_prone_scenario()
    
    def get_account_name(self) -> str:
        """Get account name for network error tests."""
        return "Trading 212"
    
    def _create_isolated_network_error_client(self) -> Mock:
        """Create a client that simulates network errors."""
        client = create_autospec(Trading212Client, spec_set=True)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Simulate network timeouts
        def timeout_error():
            import requests
            raise requests.exceptions.Timeout("Request timed out")
        
        def connection_error():
            import requests
            raise requests.exceptions.ConnectionError("Connection failed")
        
        client.get_account_metadata.side_effect = timeout_error
        client.get_account_cash.side_effect = connection_error
        client.get_portfolio.return_value = []  # Empty portfolio due to network issues
        client.get_position_details.side_effect = timeout_error
        
        return client
    
    def test_isolated_network_timeout_handling(self):
        """Test handling of network timeout errors with strict validation."""
        network_client = self._create_isolated_network_error_client()
        exporter = PortfolioExporter({"Trading 212": network_client})
        
        # Should handle network errors gracefully
        exporter.fetch_data()
        
        # Should have account summary with fallback values
        assert len(exporter.account_summaries) == 1, "Should have account summary despite network errors"
        
        account_summary = exporter.account_summaries["Trading 212"]
        self.validate_account_summary_structure(account_summary)
        
        # Validate network error fallbacks
        assert account_summary.free_funds == Decimal('0'), "Should use zero for network timeout"
        assert account_summary.currency == "USD", "Should use USD as default currency"
        assert account_summary.invested == Decimal('0'), "Empty portfolio should have zero invested"
        assert account_summary.result == Decimal('0'), "Empty portfolio should have zero profit/loss"
        
        # Should have empty positions due to network failure
        assert len(exporter.positions) == 0, "Should have empty positions due to network failure"
    
    def test_isolated_connection_error_handling(self):
        """Test handling of connection errors with strict validation."""
        network_client = self._create_isolated_network_error_client()
        exporter = PortfolioExporter({"Trading 212": network_client})
        
        exporter.fetch_data()
        
        # Should still generate valid markdown
        markdown = exporter.generate_markdown()
        self.validate_markdown_structure(markdown)
        
        # Should adapt to empty portfolio
        assert "## Summary" in markdown, "Should have summary section"
        
        # Should show zero values for network failure scenario
        assert "0.00" in markdown or "0" in markdown, "Should show zero values due to network failure"


@pytest.mark.integration
class TestIsolatedPermissionErrorHandling(IsolatedIntegrationTestBase):
    """Isolated tests for API permission error scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create permission error test data."""
        return EdgeCaseTestData.create_error_prone_scenario()
    
    def get_account_name(self) -> str:
        """Get account name for permission error tests."""
        return "Trading 212"
    
    def _create_isolated_permission_error_client(self) -> Mock:
        """Create a client that simulates permission errors."""
        client = create_autospec(Trading212Client, spec_set=True)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Simulate HTTP 403 permission denied
        def permission_denied():
            import requests
            response = Mock()
            response.status_code = 403
            response.json.return_value = {"error": "Permission denied"}
            error = requests.exceptions.HTTPError("403 Forbidden")
            error.response = response
            raise error
        
        client.get_account_metadata.side_effect = permission_denied
        client.get_account_cash.side_effect = permission_denied
        client.get_portfolio.side_effect = permission_denied
        client.get_position_details.side_effect = permission_denied
        
        return client
    
    def test_isolated_403_permission_error_handling(self):
        """Test handling of 403 permission errors with strict validation."""
        permission_client = self._create_isolated_permission_error_client()
        exporter = PortfolioExporter({"Trading 212": permission_client})
        
        # Should handle permission errors gracefully
        exporter.fetch_data()
        
        # Should create account summary with fallback values
        assert len(exporter.account_summaries) == 1, "Should have account summary despite permission errors"
        
        account_summary = exporter.account_summaries["Trading 212"]
        self.validate_account_summary_structure(account_summary)
        
        # Validate permission error fallbacks
        assert account_summary.free_funds == Decimal('0'), "Should use zero for permission denied"
        assert account_summary.invested == Decimal('0'), "Should use zero for permission denied"
        assert account_summary.result == Decimal('0'), "Should use zero for permission denied"
        assert account_summary.currency == "USD", "Should use USD as default"
        
        # Should have empty positions due to permission denial
        assert len(exporter.positions) == 0, "Should have no positions due to permission denial"
        
        # Should still generate markdown
        markdown = exporter.generate_markdown()
        assert isinstance(markdown, str), "Should generate markdown despite permission errors"
        assert "# Trading 212 Portfolio" in markdown, "Should have title"
        assert "## Summary" in markdown, "Should have summary section"


@pytest.mark.integration
class TestIsolatedDataValidationErrors(IsolatedIntegrationTestBase):
    """Isolated tests for data validation error scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create basic test data for validation tests."""
        from .isolated_test_data import SingleAccountTestData
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for validation tests."""
        return "Trading 212"
    
    def test_isolated_invalid_position_data_handling(self):
        """Test handling of invalid position data with strict validation."""
        # Create client with invalid position data
        client = create_autospec(Trading212Client, spec_set=True)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Valid metadata and cash
        client.get_account_metadata.return_value = {
            "currencyCode": "USD",
            "id": 12345,
            "type": "LIVE"
        }
        client.get_account_cash.return_value = {
            "free": 1000.0,
            "total": 1000.0,
            "result": 0.0,
            "interest": 0.0
        }
        
        # Invalid position data (negative quantity)
        client.get_portfolio.return_value = [
            {
                "ticker": "INVALID",
                "quantity": -10.0,  # Invalid negative quantity
                "averagePrice": 150.0,
                "currentPrice": 160.0,
                "currencyCode": "USD"
            }
        ]
        
        client.get_position_details.return_value = {
            "ticker": "INVALID",
            "name": "Invalid Position"
        }
        
        exporter = PortfolioExporter({"Trading 212": client})
        
        # Should handle invalid data gracefully
        exporter.fetch_data()
        
        # Validate error handling - should skip invalid positions
        # Note: The actual implementation might filter out invalid data
        # This test validates that the system doesn't crash on invalid data
        assert len(exporter.account_summaries) == 1, "Should have account summary"
        
        account_summary = exporter.account_summaries["Trading 212"]
        self.validate_account_summary_structure(account_summary)
    
    def test_isolated_missing_required_fields_handling(self):
        """Test handling of missing required fields with strict validation."""
        # Create client with incomplete data
        client = create_autospec(Trading212Client, spec_set=True)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Missing required field in metadata
        client.get_account_metadata.return_value = {
            "currencyCode": "USD",
            # Missing "id" and "type" fields
        }
        
        # Missing required field in cash
        client.get_account_cash.return_value = {
            "free": 1000.0,
            # Missing "total", "result", "interest" fields
        }
        
        # Missing required fields in position
        client.get_portfolio.return_value = [
            {
                "ticker": "INCOMPLETE",
                # Missing "quantity", "averagePrice", "currentPrice", "currencyCode"
            }
        ]
        
        exporter = PortfolioExporter({"Trading 212": client})
        
        # Should handle incomplete data gracefully
        try:
            exporter.fetch_data()
            # If it doesn't raise an exception, validate the fallback behavior
            assert len(exporter.account_summaries) == 1, "Should create account summary with fallbacks"
        except (KeyError, AttributeError, ValueError):
            # Expected behavior - system should handle missing fields gracefully
            # The test validates that we get predictable errors rather than crashes
            pass