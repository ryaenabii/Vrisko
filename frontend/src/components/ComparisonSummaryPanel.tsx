import React from 'react';
import type { ComparisonSummary } from '../types';
import StarRating from './StarRating';

interface ComparisonSummaryPanelProps {
  summary: ComparisonSummary;
}

const SummaryRow: React.FC<{ label: string; children: React.ReactNode; icon: React.ReactNode }> = ({
  label,
  children,
  icon,
}) => (
  <div className="flex gap-4 p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors">
    <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white shadow-sm shrink-0">
      {icon}
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      {children}
    </div>
  </div>
);

const ComparisonSummaryPanel: React.FC<ComparisonSummaryPanelProps> = ({ summary }) => {
  const getSym = (currency?: string) => (currency === 'INR' ? '₹' : currency === 'USD' ? '$' : '£');

  return (
    <div className="card p-6">
      <h2 className="section-heading mb-5">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
        Comparison Summary
      </h2>

      <div className="flex flex-col gap-3 mb-6">
        {summary.cheapest_listed_price && summary.cheapest_listed_price.listed_price !== null && (
          <SummaryRow
            label="Cheapest listed price"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>}
          >
            <p className="text-sm font-bold text-navy-900">
              {getSym(summary.cheapest_listed_price.currency)}
              {summary.cheapest_listed_price.listed_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} at {summary.cheapest_listed_price.retailer_name}
            </p>
          </SummaryRow>
        )}

        {summary.best_verified_deal && summary.best_verified_deal.comparable_total !== null && (
          <SummaryRow
            label="Best verified deal"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          >
            <p className="text-sm font-bold text-navy-900">
              {getSym(summary.best_verified_deal.currency)}
              {summary.best_verified_deal.comparable_total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} total at {summary.best_verified_deal.retailer_name}
            </p>
            <p className="text-xs text-slate-500">Delivery included, listing verified</p>
          </SummaryRow>
        )}

        {summary.best_conditional_offer && (
          <SummaryRow
            label="Best conditional offer"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>}
          >
            <p className="text-sm font-bold text-amber-700">
              {summary.best_conditional_offer.retailer_name}
            </p>
            <p className="text-xs text-amber-600 italic">
              ⚠ Conditional discount — verify eligibility before purchasing.
              Not included in confirmed total.
            </p>
          </SummaryRow>
        )}

        {summary.highest_rated && (
          <SummaryRow
            label="Highest customer rating"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" strokeWidth="0.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>}
          >
            <div className="flex items-center gap-2">
              <StarRating rating={summary.highest_rated.rating} size="sm" />
              <span className="text-xs text-slate-500">at {summary.highest_rated.retailer_name}</span>
            </div>
          </SummaryRow>
        )}
      </div>

      {/* Vrisko recommendation */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-teal-50 border border-blue-100">
        <p className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-2 flex items-center gap-1">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          Vrisko's Recommendation
        </p>
        <p className="text-sm text-slate-700 leading-relaxed mb-3">{summary.recommendation}</p>
        {summary.recommendation_rationale.length > 0 && (
          <ul className="flex flex-col gap-1">
            {summary.recommendation_rationale.map((r, i) => (
              <li key={i} className="text-xs text-slate-600 flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">•</span>
                {r}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default ComparisonSummaryPanel;
