import { useState } from 'react';
import { getBestLogoUrl } from '../utils/logoUtils';

interface LogoProps {
  ticker: string;
  name: string;
  size?: number;
  className?: string;
}

/**
 * Logo component that displays company/ETF logo with fallback to initials
 */
export default function Logo({ ticker, name, size = 32, className = '' }: LogoProps) {
  const [logoError, setLogoError] = useState(false);
  const logoUrl = getBestLogoUrl(ticker, name);
  const initials = name.substring(0, 2).toUpperCase();

  // If no logo URL or error loading, show initials
  const showInitials = !logoUrl || logoError;

  return (
    <div
      className={`flex items-center justify-center rounded-full bg-portfolio-card overflow-hidden ${className}`}
      style={{ width: size, height: size, minWidth: size, minHeight: size }}
    >
      {showInitials ? (
        <span className="text-xs font-bold text-portfolio-text-dim">
          {initials}
        </span>
      ) : (
        <img
          src={logoUrl}
          alt={`${name} logo`}
          className="w-full h-full object-cover"
          onError={() => setLogoError(true)}
          loading="lazy"
        />
      )}
    </div>
  );
}

