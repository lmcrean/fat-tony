/**
 * Utilities for fetching company and ETF logos
 */

/**
 * Extract base ticker from Trading 212 format
 * Examples:
 * - "NVDA_US_EQ" -> "NVDA"
 * - "VUAGl_EQ" -> "VUAG"
 * - "RMVl_EQ" -> "RMV"
 */
export function extractBaseTicker(ticker: string): string {
  // Remove common suffixes
  const cleaned = ticker.replace(/_US_EQ$/i, '')
    .replace(/_EQ$/i, '')
    .replace(/l_EQ$/i, '')
    .replace(/a_EQ$/i, '')
    .replace(/d_EQ$/i, '');
  
  return cleaned;
}

/**
 * Get ETF provider from name
 */
export function getETFProvider(name: string): 'ishares' | 'vanguard' | 'wisdomtree' | 'vaneck' | null {
  const lower = name.toLowerCase();
  if (lower.includes('ishares')) return 'ishares';
  if (lower.includes('vanguard')) return 'vanguard';
  if (lower.includes('wisdomtree')) return 'wisdomtree';
  if (lower.includes('vaneck')) return 'vaneck';
  return null;
}

/**
 * Check if ticker is a US stock (ends with _US_EQ)
 */
export function isUSStock(ticker: string): boolean {
  return /_US_EQ$/i.test(ticker);
}


/**
 * TradingView logo URL generator
 * Format varies by exchange and ticker
 */
export function getTradingViewLogoUrl(ticker: string): string | null {
  const baseTicker = extractBaseTicker(ticker);
  const lowerTicker = baseTicker.toLowerCase();
  
  // Common LSE ETF mappings
  const lseMappings: Record<string, string> = {
    'vuag': 'vusa',
    'vusa': 'vusa',
    'exic': 'daxe',
    'daxe': 'daxe',
    'iitu': 'iitu',
    'cnx1': 'cnx1',
    'fxac': 'fxac',
    'iind': 'iind',
    'r1gr': 'iwf', // iShares Russell 1000 Growth
    'rmv': 'rmv', // Rightmove
  };
  
  const mappedTicker = lseMappings[lowerTicker] || lowerTicker;
  
  // TradingView format for LSE: london--{ticker}.svg
  return `https://s3-symbol-logo.tradingview.com/london--${mappedTicker}.svg`;
}

/**
 * Get the best available logo URL
 * Tries multiple sources in order of reliability
 */
export function getBestLogoUrl(ticker: string, name: string): string | null {
  const baseTicker = extractBaseTicker(ticker);
  
  // Strategy 1: US stocks - use Clearbit via company domain
  if (isUSStock(ticker)) {
    // Common company domain mappings
    const domainMappings: Record<string, string> = {
      'nvda': 'nvidia.com',
      'pltr': 'palantir.com',
      'avgo': 'broadcom.com',
      'orcl': 'oracle.com',
      'meta': 'meta.com',
      'msft': 'microsoft.com',
      'amzn': 'amazon.com',
      'googl': 'alphabet.com',
      'aapl': 'apple.com',
      'tsla': 'tesla.com',
    };
    
    const domain = domainMappings[baseTicker.toLowerCase()] || `${baseTicker.toLowerCase()}.com`;
    return `https://logo.clearbit.com/${domain}`;
  }
  
  // Strategy 2: TradingView for LSE-listed ETFs and UK stocks
  const tvUrl = getTradingViewLogoUrl(ticker);
  if (tvUrl) return tvUrl;
  
  // Strategy 3: Provider logos for known ETFs
  const provider = getETFProvider(name);
  if (provider === 'ishares') {
    // iShares generic logo or try TradingView with specific ticker
    return getTradingViewLogoUrl(ticker);
  }
  
  if (provider === 'vanguard') {
    // Vanguard generic logo or try TradingView
    return getTradingViewLogoUrl(ticker);
  }
  
  // No logo found - will fallback to initials
  return null;
}

