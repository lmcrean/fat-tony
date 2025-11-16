import type { Position, AccountSummary, PortfolioData } from '../types/portfolio';

export function parseNumber(value: string): number {
  // Remove quotes, commas, and + signs
  const cleaned = value.replace(/[",+]/g, '').trim();
  return parseFloat(cleaned) || 0;
}

export function parseCurrency(value: string): string {
  return value.replace(/[",]/g, '').trim();
}

export function parsePositionsCSV(csvContent: string): Position[] {
  const lines = csvContent.trim().split('\n');
  const positions: Position[] = [];

  // Skip header (first line) and last empty line
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Parse CSV with proper handling of quoted values
    const values = parseCSVLine(line);
    if (values.length < 13) continue;

    positions.push({
      accountType: values[0],
      name: values[1],
      ticker: values[2],
      quantity: parseNumber(values[3]),
      priceOwnedCurrency: parseCurrency(values[4]),
      currentPriceCurrency: parseCurrency(values[5]),
      priceOwned: parseNumber(values[6]),
      priceOwnedGBP: parseNumber(values[7]),
      currentPrice: parseNumber(values[8]),
      currentPriceGBP: parseNumber(values[9]),
      valueGBP: parseNumber(values[10]),
      changeGBP: parseNumber(values[11]),
      changePercent: parseNumber(values[12]),
    });
  }

  return positions;
}

export function parseSummaryCSV(csvContent: string): Partial<PortfolioData> {
  const lines = csvContent.trim().split('\n');
  const accountSummaries: AccountSummary[] = [];
  let totalFreeFunds = 0;
  let totalPortfolio = 0;
  let totalResult = 0;
  let currency = 'GBP';
  let generatedDate = '';

  // Extract generated date from first line
  if (lines[0]?.includes('Generated on')) {
    const match = lines[0].match(/Generated on (.+)/);
    if (match) generatedDate = match[1];
  }

  let inAccountSummaries = false;
  let inCombinedTotals = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.includes('ACCOUNT SUMMARIES')) {
      inAccountSummaries = true;
      continue;
    }

    if (line.includes('COMBINED TOTALS')) {
      inAccountSummaries = false;
      inCombinedTotals = true;
      continue;
    }

    if (inAccountSummaries && line && !line.includes('ACCOUNT,FREE_FUNDS')) {
      const values = parseCSVLine(line);
      if (values.length >= 5) {
        accountSummaries.push({
          account: values[0],
          freeFunds: parseNumber(values[1]),
          portfolio: parseNumber(values[2]),
          result: parseNumber(values[3]),
          currency: parseCurrency(values[4]),
        });
      }
    }

    if (inCombinedTotals && line && !line.includes('TOTAL_FREE_FUNDS')) {
      const values = parseCSVLine(line);
      if (values.length >= 4) {
        totalFreeFunds = parseNumber(values[0]);
        totalPortfolio = parseNumber(values[1]);
        totalResult = parseNumber(values[2]);
        currency = parseCurrency(values[3]);
      }
    }
  }

  return {
    accountSummaries,
    totalFreeFunds,
    totalPortfolio,
    totalResult,
    currency,
    generatedDate,
  };
}

// Helper function to parse CSV line with quoted values
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += char;
    }
  }

  result.push(current);
  return result;
}
