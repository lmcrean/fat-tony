"""Tests for ticker symbol to name mappings."""

import pytest
from trading212_exporter.ticker_mappings import get_display_name, TICKER_TO_NAME


class TestTickerMappings:
    """Test ticker mapping functionality."""
    
    def test_ticker_mapping_exists(self):
        """Test that common tickers are in the mapping."""
        # ETF tickers
        assert "VUAGl_EQ" in TICKER_TO_NAME
        assert "FXACa_EQ" in TICKER_TO_NAME
        assert "SGLNl_EQ" in TICKER_TO_NAME
        
        # Stock tickers
        assert "PLTR_US_EQ" in TICKER_TO_NAME
        assert "NVDA_US_EQ" in TICKER_TO_NAME
    
    def test_get_display_name_with_api_name(self):
        """Test get_display_name when API provides a good name."""
        # API provides a good name - should use it
        assert get_display_name("AAPL", "Apple Inc.") == "Apple Inc."
        assert get_display_name("GOOGL", "Alphabet Inc.") == "Alphabet Inc."
    
    def test_get_display_name_with_ticker_as_api_name(self):
        """Test get_display_name when API returns ticker as name."""
        # API returns ticker as name - should use mapping
        assert get_display_name("VUAGl_EQ", "VUAGl_EQ") == "Vanguard S&P 500 (Acc)"
        assert get_display_name("PLTR_US_EQ", "PLTR_US_EQ") == "Palantir"
    
    def test_get_display_name_with_no_api_name(self):
        """Test get_display_name when API provides no name."""
        # No API name - should use mapping
        assert get_display_name("VUAGl_EQ", None) == "Vanguard S&P 500 (Acc)"
        assert get_display_name("FXACa_EQ", None) == "iShares China Large Cap (Acc)"
    
    def test_get_display_name_unmapped_ticker(self):
        """Test get_display_name with unmapped ticker."""
        # Unknown ticker - should return ticker itself
        assert get_display_name("UNKNOWN_TICKER", None) == "UNKNOWN_TICKER"
        assert get_display_name("UNKNOWN_TICKER", "UNKNOWN_TICKER") == "UNKNOWN_TICKER"
    
    def test_specific_mappings(self):
        """Test specific ticker mappings match source_of_truth."""
        mappings = {
            "VUAGl_EQ": "Vanguard S&P 500 (Acc)",
            "FXACa_EQ": "iShares China Large Cap (Acc)",
            "SGLNl_EQ": "iShares Physical Gold",
            "PLTR_US_EQ": "Palantir",
            "NVDA_US_EQ": "Nvidia",
            "RMVl_EQ": "Rightmove",
            "AVGO_US_EQ": "Broadcom",
            "ORCL_US_EQ": "Oracle",
            "SHOP_US_EQ": "Shopify",
            "MSFT_US_EQ": "Microsoft",
            "V_US_EQ": "Visa",
        }
        
        for ticker, expected_name in mappings.items():
            assert TICKER_TO_NAME[ticker] == expected_name