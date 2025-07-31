"""
Isolated integration tests for specific API scenarios.

These tests target specific API behaviors and edge cases to improve coverage.
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, call

from trading212_exporter import Trading212Client, PortfolioExporter
from .isolated_base import IsolatedIntegrationTestBase, IsolatedTestData
from .isolated_test_data import SingleAccountTestData, PerformanceTestData


@pytest.mark.integration
class TestIsolatedRateLimitingScenarios(IsolatedIntegrationTestBase):
    """Isolated tests for API rate limiting scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create test data for rate limiting tests."""
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for rate limiting tests."""
        return "Trading 212"
    
    def _create_isolated_rate_limited_client(self) -> Mock:
        """Create a client that enforces rate limiting."""
        client = Mock(spec=Trading212Client)
        client.account_name = "Trading 212"
        client._request_interval = 0.1  # Fast interval for testing
        client._last_request_time = 0
        
        test_data = self.get_test_data()
        
        # Track call times to verify rate limiting
        call_times = []
        
        def rate_limited_metadata():
            current_time = time.time()
            call_times.append(current_time)
            if len(call_times) > 1:
                time_diff = current_time - call_times[-2]
                if time_diff < client._request_interval:
                    time.sleep(client._request_interval - time_diff)
            return test_data.account_metadata
        
        def rate_limited_cash():
            current_time = time.time()
            call_times.append(current_time)
            if len(call_times) > 1:
                time_diff = current_time - call_times[-2]
                if time_diff < client._request_interval:
                    time.sleep(client._request_interval - time_diff)
            return test_data.account_cash
        
        client.get_account_metadata.side_effect = rate_limited_metadata
        client.get_account_cash.side_effect = rate_limited_cash
        client.get_portfolio.return_value = test_data.portfolio_positions
        
        def rate_limited_position_details(ticker: str):
            return test_data.position_details.get(ticker, {"ticker": ticker, "name": ticker})
        
        client.get_position_details.side_effect = rate_limited_position_details
        
        # Store call times for verification
        client._call_times = call_times
        
        return client
    
    def test_isolated_rate_limiting_enforcement(self):
        """Test that rate limiting is properly enforced with strict timing validation."""
        rate_client = self._create_isolated_rate_limited_client()
        exporter = PortfolioExporter({"Trading 212": rate_client})
        
        start_time = time.time()
        exporter.fetch_data()
        end_time = time.time()
        
        # Validate that rate limiting added appropriate delays
        total_time = end_time - start_time
        
        # Should have made at least 2 API calls (metadata + cash) with rate limiting
        min_expected_time = rate_client._request_interval
        assert total_time >= min_expected_time, \
            f"Rate limiting should add delay: expected >= {min_expected_time}s, got {total_time}s"
        
        # Validate call timing
        call_times = rate_client._call_times
        if len(call_times) >= 2:
            for i in range(1, len(call_times)):
                time_diff = call_times[i] - call_times[i-1]
                assert time_diff >= rate_client._request_interval * 0.9, \
                    f"Rate limit not enforced: {time_diff}s < {rate_client._request_interval}s"
        
        # Should still complete successfully
        assert len(exporter.account_summaries) == 1, "Should complete despite rate limiting"
        assert len(exporter.positions) > 0, "Should have positions despite rate limiting"
    
    def test_isolated_rate_limit_retry_behavior(self):
        """Test behavior when hitting rate limits with retry logic."""
        client = Mock(spec=Trading212Client)
        client.account_name = "Trading 212"
        client._request_interval = 0.05
        
        test_data = self.get_test_data()
        retry_count = 0
        
        def rate_limit_then_succeed():
            nonlocal retry_count
            retry_count += 1
            if retry_count == 1:
                # Simulate hitting rate limit on first try
                import requests
                response = Mock()
                response.status_code = 429
                response.json.return_value = {"error": "Rate limit exceeded"}
                error = requests.exceptions.HTTPError("429 Too Many Requests")
                error.response = response
                raise error
            else:
                # Succeed on retry
                return test_data.account_metadata
        
        client.get_account_metadata.side_effect = rate_limit_then_succeed
        client.get_account_cash.return_value = test_data.account_cash
        client.get_portfolio.return_value = test_data.portfolio_positions
        client.get_position_details.return_value = {"ticker": "AAPL", "name": "Apple Inc."}
        
        exporter = PortfolioExporter({"Trading 212": client})
        
        # Should handle rate limit error and retry
        exporter.fetch_data()
        
        # Validate retry occurred
        assert retry_count == 2, "Should have retried after rate limit error"
        
        # Should still complete successfully
        assert len(exporter.account_summaries) == 1, "Should complete after retry"


@pytest.mark.integration
class TestIsolatedAuthenticationScenarios(IsolatedIntegrationTestBase):
    """Isolated tests for authentication scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create test data for authentication tests."""
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for authentication tests."""
        return "Trading 212"
    
    def test_isolated_invalid_api_key_handling(self):
        """Test handling of invalid API key with strict validation."""
        client = Mock(spec=Trading212Client)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Simulate 401 Unauthorized for all endpoints
        def unauthorized_error():
            import requests
            response = Mock()
            response.status_code = 401
            response.json.return_value = {"error": "Invalid API key"}
            error = requests.exceptions.HTTPError("401 Unauthorized")
            error.response = response
            raise error
        
        client.get_account_metadata.side_effect = unauthorized_error
        client.get_account_cash.side_effect = unauthorized_error
        client.get_portfolio.side_effect = unauthorized_error
        client.get_position_details.side_effect = unauthorized_error
        
        exporter = PortfolioExporter({"Trading 212": client})
        
        # Should handle auth errors gracefully
        exporter.fetch_data()
        
        # Should create account summary with fallback values
        assert len(exporter.account_summaries) == 1, "Should have account summary despite auth error"
        
        account_summary = exporter.account_summaries["Trading 212"]
        self.validate_account_summary_structure(account_summary)
        
        # Should use fallback values for auth failure
        assert account_summary.free_funds == Decimal('0'), "Should use zero for auth failure"
        assert account_summary.invested == Decimal('0'), "Should use zero for auth failure"
        assert account_summary.result == Decimal('0'), "Should use zero for auth failure"
        assert len(exporter.positions) == 0, "Should have no positions for auth failure"
    
    def test_isolated_expired_token_handling(self):
        """Test handling of expired authentication token."""
        client = Mock(spec=Trading212Client)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        call_count = 0
        
        def token_expires_during_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                # First couple calls succeed
                test_data = self.get_test_data()
                if call_count == 1:
                    return test_data.account_metadata
                else:
                    return test_data.account_cash
            else:
                # Token expires for subsequent calls
                import requests
                response = Mock()
                response.status_code = 401
                response.json.return_value = {"error": "Token expired"}
                error = requests.exceptions.HTTPError("401 Unauthorized")
                error.response = response
                raise error
        
        client.get_account_metadata.side_effect = token_expires_during_operation
        client.get_account_cash.side_effect = token_expires_during_operation
        client.get_portfolio.side_effect = token_expires_during_operation
        client.get_position_details.side_effect = token_expires_during_operation
        
        exporter = PortfolioExporter({"Trading 212": client})
        
        # Should handle partial success / partial auth failure
        exporter.fetch_data()
        
        # Should have some data from successful calls
        assert len(exporter.account_summaries) == 1, "Should have account summary"
        
        account_summary = exporter.account_summaries["Trading 212"]
        # Should have metadata and cash from successful calls
        assert account_summary.currency == "USD", "Should have currency from successful metadata call"
        
        # But positions should be empty due to auth failure
        assert len(exporter.positions) == 0, "Should have no positions due to token expiry"


@pytest.mark.integration
class TestIsolatedPerformanceScenarios(IsolatedIntegrationTestBase):
    """Isolated tests for performance scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create large portfolio test data for performance testing."""
        return PerformanceTestData.create_large_portfolio()
    
    def get_account_name(self) -> str:
        """Get account name for performance tests."""
        return "Trading 212"
    
    def test_isolated_large_portfolio_performance(self):
        """Test performance with large portfolio using strict timing validation."""
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        # Measure fetch performance
        start_time = time.time()
        exporter.fetch_data()
        fetch_time = time.time() - start_time
        
        # Should handle large portfolio efficiently (< 2 seconds with mocks)
        assert fetch_time < 2.0, f"Large portfolio fetch took too long: {fetch_time:.2f}s"
        
        # Validate correct data volume
        assert len(exporter.positions) == test_data.expected_calculations["total_positions"], \
            f"Should have {test_data.expected_calculations['total_positions']} positions"
        
        # Measure markdown generation performance
        start_time = time.time()
        markdown = exporter.generate_markdown()
        generation_time = time.time() - start_time
        
        # Should generate markdown efficiently (< 0.5 seconds)
        assert generation_time < 0.5, f"Markdown generation took too long: {generation_time:.2f}s"
        
        # Validate substantial output
        assert len(markdown) > 5000, f"Large portfolio should generate substantial markdown: {len(markdown)} chars"
        
        # Validate all positions are included
        for position_data in test_data.portfolio_positions:
            ticker = position_data["ticker"]
            assert ticker in markdown, f"Ticker {ticker} should be in markdown"
    
    def test_isolated_memory_efficiency(self):
        """Test memory efficiency with large dataset."""
        import sys
        
        exporter = self.get_exporter()
        
        # Get baseline memory usage
        baseline_memory = sys.getsizeof(exporter)
        
        # Load large dataset
        exporter.fetch_data()
        loaded_memory = sys.getsizeof(exporter) + sum(sys.getsizeof(p) for p in exporter.positions)
        
        # Generate markdown
        markdown = exporter.generate_markdown()
        markdown_memory = sys.getsizeof(markdown)
        
        # Memory usage should be reasonable
        total_memory = loaded_memory + markdown_memory
        
        # Should not use excessive memory (< 1MB for test data)
        memory_limit = 1024 * 1024  # 1MB
        assert total_memory < memory_limit, \
            f"Memory usage excessive: {total_memory} bytes > {memory_limit} bytes"
        
        # Validate data integrity despite large volume
        test_data = self.get_test_data()
        assert len(exporter.positions) == test_data.expected_calculations["total_positions"], \
            "Should maintain data integrity with large dataset"


@pytest.mark.integration
class TestIsolatedCurrencyScenarios(IsolatedIntegrationTestBase):
    """Isolated tests for currency handling scenarios."""
    
    def create_isolated_test_data(self) -> IsolatedTestData:
        """Create multi-currency test data."""
        return SingleAccountTestData.create_usd_account()
    
    def get_account_name(self) -> str:
        """Get account name for currency tests."""
        return "Trading 212"
    
    def test_isolated_mixed_currency_position_handling(self):
        """Test handling of positions with mixed currencies in same account."""
        client = Mock(spec=Trading212Client)
        client.account_name = "Trading 212"
        client._request_interval = 5
        
        # Account in USD but with mixed currency positions
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
        
        # Mixed currency positions (USD account with GBP position)
        client.get_portfolio.return_value = [
            {
                "ticker": "AAPL",
                "quantity": 10.0,
                "averagePrice": 150.0,
                "currentPrice": 160.0,
                "currencyCode": "USD"
            },
            {
                "ticker": "VOD.L",
                "quantity": 100.0,
                "averagePrice": 1.25,
                "currentPrice": 1.30,
                "currencyCode": "GBP"  # Different currency in same account
            }
        ]
        
        def position_details_handler(ticker: str):
            details_map = {
                "AAPL": {"ticker": "AAPL", "name": "Apple Inc.", "currencyCode": "USD"},
                "VOD.L": {"ticker": "VOD.L", "name": "Vodafone Group Plc", "currencyCode": "GBP"}
            }
            return details_map.get(ticker, {"ticker": ticker, "name": ticker})
        
        client.get_position_details.side_effect = position_details_handler
        
        exporter = PortfolioExporter({"Trading 212": client})
        exporter.fetch_data()
        
        # Should handle mixed currencies correctly
        assert len(exporter.positions) == 2, "Should have both USD and GBP positions"
        
        # Validate currency preservation
        usd_positions = [p for p in exporter.positions if p.currency == "USD"]
        gbp_positions = [p for p in exporter.positions if p.currency == "GBP"]
        
        assert len(usd_positions) == 1, "Should have one USD position"
        assert len(gbp_positions) == 1, "Should have one GBP position"
        
        # Validate position details
        usd_position = usd_positions[0]
        gbp_position = gbp_positions[0]
        
        assert usd_position.ticker == "AAPL", "USD position should be AAPL"
        assert gbp_position.ticker == "VOD.L", "GBP position should be VOD.L"
        
        # Account summary should use account currency
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.currency == "USD", "Account summary should use account currency"
        
        # Generate markdown and verify currency formatting
        markdown = exporter.generate_markdown()
        assert "USD" in markdown, "Should show USD currency"
        assert "GBP" in markdown, "Should show GBP currency"
    
    def test_isolated_currency_conversion_scenarios(self):
        """Test scenarios requiring currency awareness."""
        # This test validates that the system properly preserves currency information
        # without assuming conversion rates
        
        exporter = self.get_exporter()
        test_data = self.get_test_data()
        
        exporter.fetch_data()
        
        # Validate currency consistency
        for position in exporter.positions:
            self.validate_position_structure(position)
            
            # Find corresponding test data
            position_data = next(p for p in test_data.portfolio_positions if p["ticker"] == position.ticker)
            
            # Currency should match exactly
            assert position.currency == position_data["currencyCode"], \
                f"Currency mismatch for {position.ticker}: expected {position_data['currencyCode']}, got {position.currency}"
        
        # Account summary currency should match metadata
        account_summary = exporter.account_summaries["Trading 212"]
        assert account_summary.currency == test_data.account_metadata["currencyCode"], \
            "Account summary currency should match metadata"