"""
Trading 212 API client for fetching portfolio data.
"""

import sys
import time
from typing import Dict, List

import requests


class Trading212Client:
    """Client for interacting with Trading 212 API."""
    
    BASE_URL = "https://live.trading212.com/api/v0"
    
    def __init__(self, api_key: str, account_name: str = "Trading 212"):
        """Initialize the client with API key and account name."""
        self.api_key = api_key
        self.account_name = account_name
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": api_key,
            "Content-Type": "application/json"
        })
        self._last_request_time = 0
        self._request_interval = 0.5  # 500ms between requests to respect rate limits
    
    def _rate_limit(self):
        """Implement rate limiting to avoid hitting API limits."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < self._request_interval:
            time.sleep(self._request_interval - time_since_last_request)
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict:
        """Make a request to the API with error handling."""
        self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print("Rate limit exceeded. Waiting before retry...")
                time.sleep(5)
                return self._make_request(endpoint, method, **kwargs)
            elif response.status_code == 401:
                print("Authentication failed. Please check your API key.")
                sys.exit(1)
            else:
                print(f"HTTP error occurred: {e}")
                print(f"Response: {response.text}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"Network error occurred: {e}")
            raise
    
    def get_portfolio(self) -> List[Dict]:
        """Get all portfolio positions."""
        return self._make_request("/equity/portfolio")
    
    def get_position_details(self, ticker: str) -> Dict:
        """Get detailed information for a specific position."""
        return self._make_request(f"/equity/portfolio/{ticker}")
    
    def get_account_cash(self) -> Dict:
        """Get account cash balance."""
        return self._make_request("/equity/account/cash")
    
    def get_account_metadata(self) -> Dict:
        """Get account metadata including currency."""
        return self._make_request("/equity/account/info")