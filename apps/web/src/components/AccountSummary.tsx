import { AccountSummary as AccountSummaryType } from '../types/portfolio';

interface Props {
  totalFreeFunds: number;
  totalPortfolio: number;
  totalResult: number;
  currency: string;
  accountSummaries?: AccountSummaryType[];
  generatedDate?: string;
}

export default function AccountSummary({
  totalFreeFunds,
  totalPortfolio,
  totalResult,
  currency,
  accountSummaries,
  generatedDate,
}: Props) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div className="w-full bg-portfolio-card border-t border-portfolio-border">
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Individual Account Summaries */}
        {accountSummaries && accountSummaries.length > 0 && (
          <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {accountSummaries.map((account, index) => (
              <div
                key={index}
                className="bg-portfolio-bg rounded-lg p-4 border border-portfolio-border"
              >
                <h3 className="text-portfolio-text-dim text-sm font-medium mb-3">
                  {account.account}
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-portfolio-text-dim text-xs mb-1">FREE FUNDS</div>
                    <div className="text-portfolio-text font-medium">
                      {formatCurrency(account.freeFunds)}
                    </div>
                  </div>
                  <div>
                    <div className="text-portfolio-text-dim text-xs mb-1">PORTFOLIO</div>
                    <div className="text-portfolio-text font-medium">
                      {formatCurrency(account.portfolio)}
                    </div>
                  </div>
                  <div>
                    <div className="text-portfolio-text-dim text-xs mb-1">RESULT</div>
                    <div
                      className={`font-medium ${
                        account.result >= 0 ? 'text-portfolio-green' : 'text-portfolio-red'
                      }`}
                    >
                      {account.result >= 0 ? '+' : ''}
                      {formatCurrency(account.result)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Combined Totals */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-portfolio-bg rounded-lg p-6 border border-portfolio-border">
          <div className="flex-1 min-w-[200px]">
            <div className="text-portfolio-text-dim text-xs uppercase mb-2">
              Free Funds
            </div>
            <div className="text-portfolio-text text-2xl font-semibold">
              {formatCurrency(totalFreeFunds)}
            </div>
          </div>

          <div className="flex-1 min-w-[200px]">
            <div className="text-portfolio-text-dim text-xs uppercase mb-2">
              Portfolio
            </div>
            <div className="text-portfolio-text text-2xl font-semibold">
              {formatCurrency(totalPortfolio)}
            </div>
          </div>

          <div className="flex-1 min-w-[200px]">
            <div className="text-portfolio-text-dim text-xs uppercase mb-2">
              Result
            </div>
            <div
              className={`text-2xl font-semibold ${
                totalResult >= 0 ? 'text-portfolio-green' : 'text-portfolio-red'
              }`}
            >
              {totalResult >= 0 ? '+' : ''}
              {formatCurrency(totalResult)}
            </div>
          </div>

          {generatedDate && (
            <div className="w-full mt-4 pt-4 border-t border-portfolio-border">
              <div className="text-portfolio-text-dim text-xs text-center">
                Last updated: {generatedDate}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
