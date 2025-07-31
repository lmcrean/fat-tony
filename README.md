# Trading 212 Portfolio Exporter

Export your Trading 212 portfolio to a beautifully formatted markdown file with profit/loss calculations and visual indicators.

## Features

- 📊 Fetches real-time portfolio data from Trading 212 API
- 💰 Calculates profit/loss for each position in £ and %
- 🟢🔴 Visual indicators for gains and losses
- 📋 Generates a clean markdown table with all positions
- 📈 Includes portfolio summary with total results
- 🔒 Secure API key handling via environment variables
- ⏱️ Built-in rate limiting to respect API limits

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

1. Get your API key from [Trading 212 Settings](https://app.trading212.com/settings/api)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```
   API_KEY=your_actual_api_key_here
   ```

### 3. Run the Script

```bash
python export_portfolio.py
```

The script will generate a `portfolio.md` file in the same directory.

## Output Example

The generated markdown file includes:

- **Portfolio Positions Table**: All your holdings with current values and P&L
- **Summary Section**: Total portfolio value, cash balance, and overall profit/loss

## API Documentation

This script uses the Trading 212 Public API. For more details, see the [official API documentation](https://t212public-api-docs.redoc.ly/).

## Error Handling

The script includes comprehensive error handling for:
- Missing API key
- Network errors
- API rate limits (automatic retry with backoff)
- Invalid API responses

## Requirements

- Python 3.6+
- Trading 212 account with API access enabled
- Valid API key
