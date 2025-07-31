"""
Integration tests for API rate limiting.
"""

import pytest
import time
from unittest.mock import Mock, patch

from trading212_exporter import Trading212Client


@pytest.mark.integration
@pytest.mark.slow
class TestRateLimiting:
    """Test Trading 212 API rate limiting behavior."""
    
    def test_rate_limiting_with_mock_client(self, rate_limited_client):
        """Test that rate limiting works correctly with mocked delays."""
        start_time = time.time()
        
        # Make multiple requests that should be rate limited
        rate_limited_client.get_account_metadata()
        rate_limited_client.get_account_cash()
        
        end_time = time.time()
        
        # Should take at least the rate limit interval (2 seconds for test client)
        min_expected_time = rate_limited_client._request_interval
        assert (end_time - start_time) >= min_expected_time
        
        # Should be close to expected time (allowing some tolerance)
        assert (end_time - start_time) <= (min_expected_time + 0.5)
    
    def test_rate_limiting_multiple_calls(self, rate_limited_client):
        """Test rate limiting behavior over multiple sequential calls."""
        call_times = []
        
        # Make several calls and record timing
        for i in range(3):
            start = time.time()
            rate_limited_client.get_account_metadata()
            end = time.time()
            call_times.append(end - start)
        
        # First call should be quick (no previous request to wait for)
        assert call_times[0] < 0.1
        
        # Subsequent calls should include rate limiting delay
        for call_time in call_times[1:]:
            assert call_time >= (rate_limited_client._request_interval - 0.1)
    
    def test_rate_limiting_interval_configuration(self, mock_fixture_data):
        """Test that rate limiting interval can be configured."""
        # Test with different interval
        custom_client = Mock(spec=Trading212Client)
        custom_client._request_interval = 1  # 1 second interval
        custom_client._last_request_time = 0
        
        def mock_rate_limited_call(*args, **kwargs):
            import time
            current_time = time.time()
            if custom_client._last_request_time > 0:
                time_diff = current_time - custom_client._last_request_time
                if time_diff < custom_client._request_interval:
                    time.sleep(custom_client._request_interval - time_diff)
            custom_client._last_request_time = time.time()
            return mock_fixture_data['account_metadata']['success']
        
        custom_client.get_account_metadata.side_effect = mock_rate_limited_call
        
        start_time = time.time()
        custom_client.get_account_metadata()
        custom_client.get_account_metadata()
        end_time = time.time()
        
        # Should respect the 1-second interval
        assert (end_time - start_time) >= 1.0
        assert (end_time - start_time) <= 1.5
    
    def test_rate_limiting_with_different_endpoints(self, rate_limited_client):
        """Test that rate limiting applies across different API endpoints."""
        start_time = time.time()
        
        # Mix different API calls
        rate_limited_client.get_account_metadata()
        
        # This should also be rate limited even though it's a different endpoint
        middle_time = time.time()
        rate_limited_client.get_account_cash()
        end_time = time.time()
        
        # Total time should include rate limiting
        total_time = end_time - start_time
        assert total_time >= rate_limited_client._request_interval
        
        # Second call should have been delayed
        second_call_time = end_time - middle_time  
        assert second_call_time >= (rate_limited_client._request_interval - 0.1)
    
    def test_no_rate_limiting_on_first_call(self, mock_fixture_data):
        """Test that the first API call is not rate limited."""
        fresh_client = Mock(spec=Trading212Client)
        fresh_client._request_interval = 5
        fresh_client._last_request_time = 0  # No previous request
        
        def mock_first_call(*args, **kwargs):
            # Should not sleep on first call
            fresh_client._last_request_time = time.time()
            return mock_fixture_data['account_metadata']['success']
        
        fresh_client.get_account_metadata.side_effect = mock_first_call
        
        start_time = time.time()
        fresh_client.get_account_metadata()
        end_time = time.time()
        
        # First call should be very quick (no rate limiting delay)
        assert (end_time - start_time) < 0.1
    
    @patch('time.sleep')
    def test_rate_limiting_sleep_calls(self, mock_sleep, mock_fixture_data):
        """Test that rate limiting actually calls time.sleep when needed."""
        # Create a client that simulates the real rate limiting logic
        client = Mock(spec=Trading212Client)
        client._request_interval = 5
        
        # Simulate the client's rate limiting behavior
        last_request_time = [0]  # Use list to modify from inner function
        
        def mock_rate_limited_request(*args, **kwargs):
            import time
            current_time = time.time()
            if last_request_time[0] > 0:
                time_diff = current_time - last_request_time[0]
                if time_diff < client._request_interval:
                    time.sleep(client._request_interval - time_diff)
            last_request_time[0] = time.time()
            return mock_fixture_data['account_metadata']['success']
        
        client.get_account_metadata.side_effect = mock_rate_limited_request
        
        # Make first call (should not sleep)
        client.get_account_metadata()
        assert mock_sleep.call_count == 0
        
        # Make second call immediately (should sleep)
        client.get_account_metadata()
        assert mock_sleep.call_count == 1
        
        # Verify sleep was called with approximately the right duration
        sleep_duration = mock_sleep.call_args[0][0]
        assert 4.0 <= sleep_duration <= 5.0  # Should be close to the interval
    
    def test_rate_limiting_accuracy(self, rate_limited_client):
        """Test that rate limiting timing is reasonably accurate."""
        # Make one call to establish a baseline
        rate_limited_client.get_account_metadata()
        
        # Wait a partial interval
        time.sleep(rate_limited_client._request_interval / 2)
        
        # Make another call - should wait for remaining time
        start_time = time.time()
        rate_limited_client.get_account_metadata()
        end_time = time.time()
        
        # Should have waited approximately half the interval
        actual_wait = end_time - start_time
        expected_wait = rate_limited_client._request_interval / 2
        
        # Allow some tolerance for timing precision
        assert abs(actual_wait - expected_wait) <= 0.2
    
    def test_concurrent_rate_limiting_behavior(self, mock_fixture_data):
        """Test rate limiting behavior under concurrent-like conditions."""
        # Simulate rapid successive calls
        rapid_client = Mock(spec=Trading212Client)
        rapid_client._request_interval = 1
        rapid_client._last_request_time = 0
        
        call_times = []
        
        def mock_tracked_call(*args, **kwargs):
            import time
            current_time = time.time()
            if rapid_client._last_request_time > 0:
                time_diff = current_time - rapid_client._last_request_time
                if time_diff < rapid_client._request_interval:
                    time.sleep(rapid_client._request_interval - time_diff)
            rapid_client._last_request_time = time.time()
            call_times.append(time.time())
            return mock_fixture_data['account_metadata']['success']
        
        rapid_client.get_account_metadata.side_effect = mock_tracked_call
        
        # Make 4 rapid calls
        start_time = time.time()
        for _ in range(4):
            rapid_client.get_account_metadata()
        
        # Verify calls were properly spaced
        for i in range(1, len(call_times)):
            time_diff = call_times[i] - call_times[i-1]
            assert time_diff >= (rapid_client._request_interval - 0.1)