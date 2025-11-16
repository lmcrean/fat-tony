import { useState, useEffect } from 'react';
import PortfolioTable from './components/PortfolioTable';
import AccountSummary from './components/AccountSummary';
import AccountFilter from './components/AccountFilter';
import type { PortfolioData } from './types/portfolio';
import { parsePositionsCSV, parseSummaryCSV } from './utils/csvParser';

function App() {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [selectedAccount, setSelectedAccount] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        // Load both CSV files
        const [positionsResponse, summaryResponse] = await Promise.all([
          fetch('/output/portfolio_positions_FINAL.csv'),
          fetch('/output/portfolio_summary.csv'),
        ]);

        if (!positionsResponse.ok || !summaryResponse.ok) {
          throw new Error('Failed to load CSV files');
        }

        const positionsText = await positionsResponse.text();
        const summaryText = await summaryResponse.text();

        // Parse the data
        const positions = parsePositionsCSV(positionsText);
        const summaryData = parseSummaryCSV(summaryText);

        // Combine into PortfolioData
        setPortfolioData({
          positions,
          accountSummaries: summaryData.accountSummaries || [],
          totalFreeFunds: summaryData.totalFreeFunds || 0,
          totalPortfolio: summaryData.totalPortfolio || 0,
          totalResult: summaryData.totalResult || 0,
          currency: summaryData.currency || 'GBP',
          generatedDate: summaryData.generatedDate || '',
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-portfolio-bg flex items-center justify-center">
        <div className="text-portfolio-text text-xl">Loading portfolio data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-portfolio-bg flex items-center justify-center">
        <div className="text-portfolio-red text-xl">Error: {error}</div>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="min-h-screen bg-portfolio-bg flex items-center justify-center">
        <div className="text-portfolio-text text-xl">No data available</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-portfolio-bg">
      {/* Header */}
      <div className="border-b border-portfolio-border bg-portfolio-card">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold text-portfolio-text mb-2">
            Trading 212 Portfolio
          </h1>
          <p className="text-portfolio-text-dim">
            Track your investments and performance
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <AccountFilter
          selectedAccount={selectedAccount}
          onAccountChange={setSelectedAccount}
        />

        <div className="bg-portfolio-card rounded-lg border border-portfolio-border overflow-hidden">
          <PortfolioTable
            positions={portfolioData.positions}
            accountFilter={selectedAccount}
          />
        </div>
      </div>

      {/* Summary Footer */}
      <div className="fixed bottom-0 left-0 right-0">
        <AccountSummary
          totalFreeFunds={portfolioData.totalFreeFunds}
          totalPortfolio={portfolioData.totalPortfolio}
          totalResult={portfolioData.totalResult}
          currency={portfolioData.currency}
          accountSummaries={portfolioData.accountSummaries}
          generatedDate={portfolioData.generatedDate}
        />
      </div>

      {/* Spacer to prevent content from being hidden behind fixed footer */}
      <div className="h-64"></div>
    </div>
  );
}

export default App;
