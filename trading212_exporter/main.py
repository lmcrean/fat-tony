"""
Main entry point for the Trading 212 Portfolio Exporter.
"""

import argparse
import os
import sys
from dotenv import load_dotenv

from .client import Trading212Client
from .exporter import PortfolioExporter


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Export Trading 212 portfolio data')
    parser.add_argument('--format', choices=['markdown', 'csv', 'both'], default='both',
                      help='Export format (default: both)')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for multiple API keys (new format)
    api_key_isa = os.getenv('API_KEY_STOCKS_ISA')
    api_key_invest = os.getenv('API_KEY_INVEST_ACCOUNT')
    
    # Check for legacy single API key
    api_key_legacy = os.getenv('API_KEY')
    
    # Determine which API keys are available
    clients = {}
    
    if api_key_isa:
        clients['Stocks & Shares ISA'] = Trading212Client(api_key_isa, account_name='Stocks & Shares ISA')
    
    if api_key_invest:
        clients['Invest Account'] = Trading212Client(api_key_invest, account_name='Invest Account')
    
    if api_key_legacy and not clients:
        clients['Trading 212'] = Trading212Client(api_key_legacy, account_name='Trading 212')
    
    if not clients:
        print("Error: No API keys found in .env file")
        print("Please create a .env file with your Trading 212 API key(s):")
        print("For single account: API_KEY=your_api_key_here")
        print("For multiple accounts:")
        print("  API_KEY_STOCKS_ISA=your_isa_api_key")
        print("  API_KEY_INVEST_ACCOUNT=your_invest_api_key")
        sys.exit(1)
    
    try:
        # Initialize exporter with all clients
        exporter = PortfolioExporter(clients)

        # Fetch data from all accounts
        exporter.fetch_data()

        # Fetch order history (buy/sell transactions)
        print("\n" + "="*60)
        print("Fetching transaction history...")
        print("="*60)
        exporter.fetch_order_history()

        # Export based on format choice
        if args.format in ['markdown', 'both']:
            exporter.save_to_file()

        if args.format in ['csv', 'both']:
            exporter.save_to_csv()
            exporter.save_history_to_csv()
        
    except KeyboardInterrupt:
        print("\nExport cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()