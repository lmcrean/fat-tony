import { useState, useMemo } from 'react';
import type { Position } from '../types/portfolio';
import Logo from './Logo';

interface Props {
  positions: Position[];
  accountFilter?: string;
}

type SortKey = keyof Position | null;
type SortDirection = 'asc' | 'desc';

export default function PortfolioTable({ positions, accountFilter }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('valueGBP');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const filteredPositions = useMemo(() => {
    let filtered = positions;
    if (accountFilter && accountFilter !== 'All') {
      filtered = positions.filter(p =>
        accountFilter === 'ISA' ? p.accountType === 'ISA' : p.accountType === 'Trading'
      );
    }
    return filtered;
  }, [positions, accountFilter]);

  const sortedPositions = useMemo(() => {
    if (!sortKey) return filteredPositions;

    return [...filteredPositions].sort((a, b) => {
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
  }, [filteredPositions, sortKey, sortDirection]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatNumber = (value: number, decimals = 2) => {
    return value.toLocaleString('en-GB', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const getCurrencySymbol = (currency: string) => {
    switch (currency) {
      case 'GBX':
        return 'p';
      case 'USD':
        return '$';
      case 'EUR':
        return '€';
      case 'GBP':
        return '£';
      default:
        return currency;
    }
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
    <div className="w-full overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-portfolio-border">
            <th
              className="text-left py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
              onClick={() => handleSort('accountType')}
            >
              <div className="flex items-center gap-2">
                <SortIcon column="accountType" />
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
                SHARES <SortIcon column="quantity" />
              </div>
            </th>
            <th
              className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
              onClick={() => handleSort('valueGBP')}
            >
              <div className="flex items-center justify-end gap-2">
                MARKET VALUE <SortIcon column="valueGBP" />
              </div>
            </th>
            <th
              className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
              onClick={() => handleSort('priceOwnedGBP')}
            >
              <div className="flex items-center justify-end gap-2">
                AVERAGE PRICE <SortIcon column="priceOwnedGBP" />
              </div>
            </th>
            <th
              className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
              onClick={() => handleSort('currentPriceGBP')}
            >
              <div className="flex items-center justify-end gap-2">
                CURRENT PRICE <SortIcon column="currentPriceGBP" />
              </div>
            </th>
            <th
              className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
              onClick={() => handleSort('changeGBP')}
            >
              <div className="flex items-center justify-end gap-2">
                RESULT <SortIcon column="changeGBP" />
              </div>
            </th>
            <th
              className="text-right py-4 px-4 text-portfolio-text-dim text-xs font-medium uppercase cursor-pointer hover:text-portfolio-text transition-colors"
              onClick={() => handleSort('changePercent')}
            >
              <div className="flex items-center justify-end gap-2">
                RESULT % <SortIcon column="changePercent" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedPositions.map((position, index) => (
            <tr
              key={`${position.ticker}-${index}`}
              className="border-b border-portfolio-border hover:bg-portfolio-card/50 transition-colors"
            >
              <td className="py-4 px-4">
                <div className="flex items-center gap-2">
                  <div 
                    className={`w-4 h-4 rounded ${
                      position.accountType === 'ISA'
                        ? 'bg-blue-500'
                        : 'bg-purple-500'
                    } relative group cursor-help`}
                    title={position.accountType === 'ISA' ? 'ISA Account' : 'Trading Account'}
                  >
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-portfolio-card border border-portfolio-border rounded text-xs text-portfolio-text whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                      {position.accountType === 'ISA' ? 'ISA Account' : 'Trading Account'}
                    </div>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4">
                <div className="flex items-center gap-3">
                  <Logo ticker={position.ticker} name={position.name} size={32} />
                  <div>
                    <div className="text-portfolio-text font-medium">{position.name}</div>
                    <div className="text-portfolio-text-dim text-xs">{position.ticker}</div>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4 text-right text-portfolio-text">
                {formatNumber(position.quantity, 3)}
              </td>
              <td className="py-4 px-4 text-right text-portfolio-text font-medium">
                {formatCurrency(position.valueGBP)}
              </td>
              <td className="py-4 px-4 text-right text-portfolio-text-dim">
                {getCurrencySymbol(position.priceOwnedCurrency)}
                {formatNumber(position.priceOwned)}
              </td>
              <td className={`py-4 px-4 text-right ${
                position.changeGBP >= 0 ? 'text-portfolio-green' : 'text-portfolio-red'
              }`}>
                {getCurrencySymbol(position.currentPriceCurrency)}
                {formatNumber(position.currentPrice)}
              </td>
              <td className={`py-4 px-4 text-right font-medium ${
                position.changeGBP >= 0 ? 'text-portfolio-green' : 'text-portfolio-red'
              }`}>
                {position.changeGBP >= 0 ? '+' : ''}{formatCurrency(position.changeGBP)}
              </td>
              <td className={`py-4 px-4 text-right font-medium ${
                position.changePercent >= 0 ? 'text-portfolio-green' : 'text-portfolio-red'
              }`}>
                {formatPercent(position.changePercent)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
