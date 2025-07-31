"""
Main entry point for the Trading 212 Portfolio Exporter.
"""

import os
import sys
from dotenv import load_dotenv

from .client import Trading212Client
from .exporter import PortfolioExporter


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('API_KEY')
    if not api_key:
        print("Error: API_KEY not found in .env file")
        print("Please create a .env file with your Trading 212 API key:")
        print("API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        # Initialize client and exporter
        client = Trading212Client(api_key)
        exporter = PortfolioExporter(client)
        
        # Fetch data
        exporter.fetch_data()
        
        # Generate and save markdown
        exporter.save_to_file()
        
    except KeyboardInterrupt:
        print("\nExport cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()