"""
Ticker symbol to full name mappings for Trading 212 instruments.

This module provides mappings for ticker symbols that don't return proper names
from the Trading 212 API, particularly for ETFs and funds.
"""

# Mapping of ticker symbols to their full display names
TICKER_TO_NAME = {
    # ETFs and Funds - ISA Account
    "VUAGl_EQ": "Vanguard S&P 500 (Acc)",
    "FXACa_EQ": "iShares China Large Cap (Acc)",
    "EXICd_EQ": "iShares Core DAX DE (Dist)",
    "IINDl_EQ": "iShares MSCI India (Acc)",
    
    # ETFs and Funds - Invest Account
    "IITU_EQ": "iShares S&P 500 Information Technology Sector (Acc)",
    "INTLl_EQ": "WisdomTree Artificial Intelligence (Acc)",
    "SGLNl_EQ": "iShares Physical Gold",
    "CNX1_EQ": "iShares NASDAQ 100 (Acc)",
    "RMVl_EQ": "Rightmove",
    "R1GRl_EQ": "iShares Russell 1000 Growth",
    "BLKCa_EQ": "iShares Blockchain Technology",
    "VGERl_EQ": "Vanguard Germany All Cap",
    "SMGBl_EQ": "VanEck Semiconductor (Acc)",
    "VWRPl_EQ": "Vanguard FTSE All-World (Acc)",
    "RBODl_EQ": "iShares Automation & Robotics (Dist)",
    
    # US Stocks
    "PLTR_US_EQ": "Palantir",
    "NVDA_US_EQ": "Nvidia",
    "ORCL_US_EQ": "Oracle",
    "AVGO_US_EQ": "Broadcom",
    "SHOP_US_EQ": "Shopify",
    "MSFT_US_EQ": "Microsoft",
    "V_US_EQ": "Visa",
    "SPOT_US_EQ": "Spotify Technology",
    "FB_US_EQ": "Meta Platforms",
    "META_US_EQ": "Meta Platforms",  # Alternative ticker
    "MA_US_EQ": "Mastercard",
    "NFLX_US_EQ": "Netflix",
    "AAXN_US_EQ": "Axon Enterprise",
    "GOOGL_US_EQ": "Alphabet (Class A)",
    "UBER_US_EQ": "Uber Technologies",
    "OAC_US_EQ": "Hims & Hers Health",
    "HIMS_US_EQ": "Hims & Hers Health",  # Alternative ticker
    "RDDT_US_EQ": "Reddit",
    "MSTR_US_EQ": "MicroStrategy",
    "ASML_US_EQ": "ASML",
    "AMZN_US_EQ": "Amazon",
    "PGR_US_EQ": "Progressive",
    "ISRG_US_EQ": "Intuitive Surgical",
    
    # Special case for Figma (private company)
    "FIGMA": "Figma",
    "FIGMA_US_EQ": "Figma",
    "FIG_US_EQ": "Figma",
}

def get_display_name(ticker: str, api_name: str = None) -> str:
    """
    Get the display name for a ticker symbol.
    
    Args:
        ticker: The ticker symbol
        api_name: The name returned by the API (if any)
        
    Returns:
        The display name to use
    """
    # If API provided a meaningful name (not just the ticker), use it
    if api_name and api_name != ticker and not api_name.endswith("_EQ"):
        return api_name
    
    # Otherwise, look up in our mapping
    return TICKER_TO_NAME.get(ticker, ticker)