import { useState, useMemo } from 'react';
import type { BuyHistory } from '../types/portfolio';

interface Props {
  buyHistory: BuyHistory[];
}

type SortKey = keyof BuyHistory | null;
type SortDirection = 'asc' | 'desc';

export default function BuyHistoryTable({ buyHistory }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const sortedHistory = useMemo(() => {
    if (!sortKey) return buyHistory;

    return [...buyHistory].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return 0;
    });
  }, [buyHistory, sortKey, sortDirection]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
  };

  const formatCurrency = (value: number | string) => {
    if (value === 'N/A') return 'N/A';
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 2,
    }).format(numValue);
  };

  const formatNumber = (value: number, decimals = 2) => {
    return value.toLocaleString('en-GB', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getPerformanceValue = (perf: string | number): number | null => {
    if (perf === 'N/A') return null;
    return typeof perf === 'string' ? parseFloat(perf) : perf;
  };

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return <span className="text-portfolio-text-dim opacity-30">▼</span>;
    return (
      <span className="text-blue-400">
        {sortDirection === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  return (
    <div className="w-full">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-portfolio-border">
              <th
                className="text-left py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('date')}
              >
                <div className="flex items-center gap-2">
                  DATE <SortIcon column="date" />
                </div>
              </th>
              <th
                className="text-left py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-2">
                  NAME <SortIcon column="name" />
                </div>
              </th>
              <th
                className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('quantity')}
              >
                <div className="flex items-center justify-end gap-2">
                  QUANTITY <SortIcon column="quantity" />
                </div>
              </th>
              <th
                className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('price')}
              >
                <div className="flex items-center justify-end gap-2">
                  PRICE <SortIcon column="price" />
                </div>
              </th>
              <th
                className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('totalValue')}
              >
                <div className="flex items-center justify-end gap-2">
                  TOTAL <SortIcon column="totalValue" />
                </div>
              </th>
              <th className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase">
                FEES †
              </th>
              <th
                className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('currentPrice')}
              >
                <div className="flex items-center justify-end gap-2">
                  CURRENT PRICE <SortIcon column="currentPrice" />
                </div>
              </th>
              <th
                className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('currentValue')}
              >
                <div className="flex items-center justify-end gap-2">
                  CURRENT VALUE <SortIcon column="currentValue" />
                </div>
              </th>
              <th
                className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
                onClick={() => handleSort('performance')}
              >
                <div className="flex items-center justify-end gap-2">
                  PERFORMANCE <SortIcon column="performance" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedHistory.map((order, index) => {
              const perfValue = getPerformanceValue(order.performance);
              const isPositive = perfValue !== null && perfValue >= 0;
              const isNegative = perfValue !== null && perfValue < 0;

              return (
                <tr
                  key={`${order.ticker}-${index}`}
                  className="border-b border-portfolio-border hover:bg-portfolio-card/50 transition-colors"
                >
                  <td className="py-4 px-4 text-portfolio-text-dim text-sm">
                    {formatDate(order.date)}
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-portfolio-card flex items-center justify-center text-xs font-bold">
                        {order.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-portfolio-text font-medium">{order.name}</div>
                        <div className="text-portfolio-text-dim text-xs">{order.ticker}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right text-portfolio-text">
                    {formatNumber(order.quantity, 3)}
                  </td>
                  <td className="py-4 px-4 text-right text-portfolio-text-dim">
                    £{formatNumber(order.price)}
                  </td>
                  <td className="py-4 px-4 text-right text-portfolio-text font-medium">
                    {formatCurrency(order.totalValue)}
                  </td>
                  <td className="py-4 px-4 text-right text-portfolio-text-dim text-xs">
                    {order.fees}
                  </td>
                  <td className="py-4 px-4 text-right text-portfolio-text">
                    {order.currentPrice === 'N/A' ? (
                      <span className="text-portfolio-text-dim">N/A</span>
                    ) : (
                      <>£{formatNumber(typeof order.currentPrice === 'number' ? order.currentPrice : parseFloat(order.currentPrice as string))}</>
                    )}
                  </td>
                  <td className="py-4 px-4 text-right text-portfolio-text">
                    {order.currentValue === 'N/A' ? (
                      <span className="text-portfolio-text-dim">N/A</span>
                    ) : (
                      formatCurrency(order.currentValue)
                    )}
                  </td>
                  <td className={`py-4 px-4 text-right font-medium ${
                    order.performance === 'N/A'
                      ? 'text-portfolio-text-dim'
                      : isPositive
                      ? 'text-portfolio-green'
                      : isNegative
                      ? 'text-portfolio-red'
                      : 'text-portfolio-text-dim'
                  }`}>
                    {order.performance === 'N/A' ? (
                      'N/A'
                    ) : (
                      <div>
                        <div>{perfValue !== null && perfValue >= 0 ? '+' : ''}{formatCurrency(order.performance)}</div>
                        <div className="text-xs">{order.performancePercent}</div>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-4 px-4 text-portfolio-text-dim text-xs">
        † Fees are not available via Trading 212 API
      </div>
    </div>
  );
}
