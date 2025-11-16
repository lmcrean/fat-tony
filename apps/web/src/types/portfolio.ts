export interface Position {
  accountType: string;
  name: string;
  ticker: string;
  quantity: number;
  priceOwnedCurrency: string;
  currentPriceCurrency: string;
  priceOwned: number;
  priceOwnedGBP: number;
  currentPrice: number;
  currentPriceGBP: number;
  valueGBP: number;
  changeGBP: number;
  changePercent: number;
}

export interface AccountSummary {
  account: string;
  freeFunds: number;
  portfolio: number;
  result: number;
  currency: string;
}

export interface PortfolioData {
  positions: Position[];
  accountSummaries: AccountSummary[];
  totalFreeFunds: number;
  totalPortfolio: number;
  totalResult: number;
  currency: string;
  generatedDate: string;
}
