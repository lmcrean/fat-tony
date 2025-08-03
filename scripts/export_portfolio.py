#!/usr/bin/env python3
"""
Trading 212 Portfolio Exporter
Connects to Trading 212 API and exports portfolio data to a markdown file.

This is the legacy entry point. For modular imports, use:
from trading212_exporter import Trading212Client, PortfolioExporter
"""

# Import all classes from the modular package for backward compatibility
from trading212_exporter import Position, AccountSummary, Trading212Client, PortfolioExporter
from trading212_exporter.main import main

if __name__ == "__main__":
    main()