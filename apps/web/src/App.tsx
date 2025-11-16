import { useState, useEffect } from 'react';
import PortfolioTable from './components/PortfolioTable';
import BuyHistoryTable from './components/BuyHistoryTable';
import SellHistoryTable from './components/SellHistoryTable';
import AccountSummary from './components/AccountSummary';
import AccountFilter from './components/AccountFilter';
import type { PortfolioData, BuyHistory, SellHistory } from './types/portfolio';
import { parsePositionsCSV, parseSummaryCSV, parseBuyHistoryCSV, parseSellHistoryCSV } from './utils/csvParser';

type TabType = 'portfolio' | 'buy-history' | 'sell-history';

function App() {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [buyHistory, setBuyHistory] = useState<BuyHistory[]>([]);
  const [sellHistory, setSellHistory] = useState<SellHistory[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('portfolio');
  const [selectedAccount, setSelectedAccount] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        // Load all CSV files
        const [positionsResponse, summaryResponse, buyHistoryResponse, sellHistoryResponse] = await Promise.all([
          fetch('/output/portfolio_positions_FINAL.csv'),
          fetch('/output/portfolio_summary.csv'),
          fetch('/output/buy_history.csv'),
          fetch('/output/sell_history.csv'),
        ]);

        if (!positionsResponse.ok || !summaryResponse.ok) {
          throw new Error('Failed to load portfolio CSV files');
        }

        const positionsText = await positionsResponse.text();
        const summaryText = await summaryResponse.text();

        // Parse portfolio data
        const positions = parsePositionsCSV(positionsText);
        const summaryData = parseSummaryCSV(summaryText);

        // Parse history data (optional - may not exist yet)
        if (buyHistoryResponse.ok) {
          const buyHistoryText = await buyHistoryResponse.text();
          const buyData = parseBuyHistoryCSV(buyHistoryText);
          setBuyHistory(buyData);
        }

        if (sellHistoryResponse.ok) {
          const sellHistoryText = await sellHistoryResponse.text();
          const sellData = parseSellHistoryCSV(sellHistoryText);
          setSellHistory(sellData);
        }

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
        {/* Tab Navigation */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setActiveTab('portfolio')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'portfolio'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-portfolio-card text-portfolio-text-dim hover:text-portfolio-text hover:bg-portfolio-card/80 border border-portfolio-border'
            }`}
          >
            Portfolio
          </button>
          <button
            onClick={() => setActiveTab('buy-history')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'buy-history'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-portfolio-card text-portfolio-text-dim hover:text-portfolio-text hover:bg-portfolio-card/80 border border-portfolio-border'
            }`}
          >
            Buy History
            {buyHistory.length > 0 && (
              <span className="ml-2 text-xs opacity-70">({buyHistory.length})</span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('sell-history')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'sell-history'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-portfolio-card text-portfolio-text-dim hover:text-portfolio-text hover:bg-portfolio-card/80 border border-portfolio-border'
            }`}
          >
            Sell History
            {sellHistory.length > 0 && (
              <span className="ml-2 text-xs opacity-70">({sellHistory.length})</span>
            )}
          </button>
        </div>

        {/* Account Filter (only show for portfolio tab) */}
        {activeTab === 'portfolio' && (
          <AccountFilter
            selectedAccount={selectedAccount}
            onAccountChange={setSelectedAccount}
          />
        )}

        {/* Content based on active tab */}
        <div className="bg-portfolio-card rounded-lg border border-portfolio-border overflow-hidden">
          {activeTab === 'portfolio' && (
            <PortfolioTable
              positions={portfolioData.positions}
              accountFilter={selectedAccount}
            />
          )}

          {activeTab === 'buy-history' && (
            buyHistory.length > 0 ? (
              <BuyHistoryTable buyHistory={buyHistory} />
            ) : (
              <div className="p-12 text-center text-portfolio-text-dim">
                <p>No buy history available. Run the exporter to fetch transaction history.</p>
              </div>
            )
          )}

          {activeTab === 'sell-history' && (
            sellHistory.length > 0 ? (
              <SellHistoryTable sellHistory={sellHistory} />
            ) : (
              <div className="p-12 text-center text-portfolio-text-dim">
                <p>No sell history available. Run the exporter to fetch transaction history.</p>
              </div>
            )
          )}
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
