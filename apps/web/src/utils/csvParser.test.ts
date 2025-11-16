import { describe, it, expect } from 'vitest';
import { parseNumber, parseCurrency, parsePositionsCSV, parseSummaryCSV } from './csvParser';

describe('csvParser utilities', () => {
  describe('parseNumber', () => {
    it('should parse a regular number', () => {
      expect(parseNumber('123.45')).toBe(123.45);
    });

    it('should parse number with commas', () => {
      expect(parseNumber('1,234.56')).toBe(1234.56);
    });

    it('should parse number with quotes', () => {
      expect(parseNumber('"1,234.56"')).toBe(1234.56);
    });

    it('should parse number with plus sign', () => {
      expect(parseNumber('+123.45')).toBe(123.45);
    });

    it('should handle negative numbers', () => {
      expect(parseNumber('-123.45')).toBe(-123.45);
    });

    it('should return 0 for invalid input', () => {
      expect(parseNumber('abc')).toBe(0);
    });
  });

  describe('parseCurrency', () => {
    it('should remove quotes and commas', () => {
      expect(parseCurrency('"GBP"')).toBe('GBP');
      expect(parseCurrency('USD')).toBe('USD');
    });
  });

  describe('parsePositionsCSV', () => {
    it('should parse a valid CSV line', () => {
      const csv = `Account Type,Name,Ticker,Quantity of Shares,Price owned Currency,Current Price Currency,Price Owned,Price Owned (GBP),Current Price,Current Price (GBP),Value (GBP),Change (GBP),Change %
Trading,Microsoft,MSFT_US_EQ,0.138,USD,USD,415.80,328.48,510.35,403.18,70.43,+13.05,22.74`;

      const positions = parsePositionsCSV(csv);

      expect(positions).toHaveLength(1);
      expect(positions[0].name).toBe('Microsoft');
      expect(positions[0].ticker).toBe('MSFT_US_EQ');
      expect(positions[0].quantity).toBe(0.138);
      expect(positions[0].changeGBP).toBe(13.05);
      expect(positions[0].changePercent).toBe(22.74);
    });

    it('should handle multiple positions', () => {
      const csv = `Account Type,Name,Ticker,Quantity of Shares,Price owned Currency,Current Price Currency,Price Owned,Price Owned (GBP),Current Price,Current Price (GBP),Value (GBP),Change (GBP),Change %
Trading,Microsoft,MSFT_US_EQ,0.138,USD,USD,415.80,328.48,510.35,403.18,70.43,+13.05,22.74
ISA,Amazon,AMZN_US_EQ,1.43,USD,USD,227.49,179.72,235.52,186.06,336.79,+11.48,3.53`;

      const positions = parsePositionsCSV(csv);
      expect(positions).toHaveLength(2);
    });
  });

  describe('parseSummaryCSV', () => {
    it('should parse summary CSV correctly', () => {
      const csv = `Trading 212 Portfolio Summary - Generated on 2025-11-16 11:02:10

ACCOUNT SUMMARIES
ACCOUNT,FREE_FUNDS,PORTFOLIO,RESULT,CURRENCY
Stocks & Shares ISA,"7,538.58","11,082.36",+577.68,GBP
Invest Account,0.14,"197,390.89","+44,898.07",GBP

COMBINED TOTALS
TOTAL_FREE_FUNDS,TOTAL_PORTFOLIO,TOTAL_RESULT,CURRENCY
"7,538.72","208,473.25","+45,475.75",GBP`;

      const summary = parseSummaryCSV(csv);

      expect(summary.generatedDate).toBe('2025-11-16 11:02:10');
      expect(summary.accountSummaries).toHaveLength(2);
      expect(summary.accountSummaries?.[0].account).toBe('Stocks & Shares ISA');
      expect(summary.totalFreeFunds).toBeCloseTo(7538.72);
      expect(summary.totalPortfolio).toBeCloseTo(208473.25);
      expect(summary.totalResult).toBeCloseTo(45475.75);
    });
  });
});
