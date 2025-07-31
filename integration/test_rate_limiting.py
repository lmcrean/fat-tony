"""
Integration tests for API rate limiting.
"""

import pytest
import time


@pytest.mark.integration
@pytest.mark.slow
class TestRateLimiting:
    """Test Trading 212 API rate limiting."""
    
    def test_rate_limiting(self, api_client):
        """Test that rate limiting works correctly."""
        start_time = time.time()
        
        # Make multiple requests
        api_client.get_account_metadata()
        api_client.get_account_cash()
        
        end_time = time.time()
        
        # Should take at least the rate limit interval
        min_expected_time = api_client._request_interval
        assert (end_time - start_time) >= min_expected_time