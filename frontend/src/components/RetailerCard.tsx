import React from 'react';
import type { RetailerOffer } from '../types';
import StarRating from './StarRating';

interface RetailerCardProps {
  offer: RetailerOffer;
  rank: number;
  isBestDeal?: boolean;
  isCheapest?: boolean;
  isHighestRated?: boolean;
  /** True when this offer has the best potential conditional price
   *  (after applying a known-amount conditional discount).
   *  NEVER implies the discount is confirmed or applicable. */
  isBestConditional?: boolean;
}

const ConditionBadge: React.FC<{ condition: RetailerOffer['condition'] }> = ({ condition }) => {
  const map: Record<string, string> = {
    new: 'badge-green',
    refurbished: 'badge-yellow',
    used: 'badge-orange',
    open_box: 'badge-blue',
    unknown: 'badge-slate',
  };
  return <span className={`badge ${map[condition] ?? 'badge-slate'}`}>{condition.replace('_', ' ')}</span>;
};

const VerifiedIcon: React.FC<{ verified: boolean; size?: number }> = ({ verified, size = 14 }) =>
  verified ? (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" className="inline text-emerald-500">
      <circle cx="10" cy="10" r="9" fill="#dcfce7" />
      <path d="M6 10l3 3 5-5" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ) : (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" className="inline text-slate-400">
      <circle cx="10" cy="10" r="9" fill="#f1f5f9" />
      <path d="M10 6v5M10 14v.5" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );

const InfoRow: React.FC<{ label: string; value: React.ReactNode; verified?: boolean }> = ({
  label,
  value,
  verified,
}) => (
  <div className="flex items-start justify-between gap-2 py-2 border-b border-slate-100 last:border-0">
    <span className="text-xs text-slate-500 font-medium shrink-0">{label}</span>
    <span className="text-xs font-semibold text-slate-800 text-right flex items-center gap-1">
      {verified !== undefined && <VerifiedIcon verified={verified} />}
      {value}
    </span>
  </div>
);

const RetailerCard: React.FC<RetailerCardProps> = ({
  offer,
  rank,
  isBestDeal,
  isCheapest,
  isHighestRated,
  isBestConditional,
}) => {
  const isUnavailable =
    offer.availability === 'unavailable' ||
    offer.availability === 'unknown' ||
    offer.listed_price === null;

  const hasBadge = isBestDeal || isCheapest || isHighestRated || isBestConditional;
  const sym = offer.currency === 'INR' ? '₹' : offer.currency === 'USD' ? '$' : '£';

  return (
    <div
      className={`card p-5 fade-slide-in relative overflow-hidden ${
        isBestDeal ? 'ring-2 ring-blue-500' : ''
      } ${!offer.exact_model_match || isUnavailable ? 'opacity-90' : ''}`}
      style={{ animationDelay: `${rank * 80}ms` }}
    >
      {/* Best deal glow */}
      {isBestDeal && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, rgba(59,130,246,0.04) 0%, rgba(13,148,136,0.04) 100%)',
          }}
        />
      )}

      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base font-bold text-navy-900">{offer.retailer_name}</h3>
            {offer.is_verified && (
              <span className="badge badge-teal">
                <VerifiedIcon verified size={11} /> Verified
              </span>
            )}
            {isUnavailable && (
              <span className="badge badge-slate">
                {offer.availability === 'unknown' ? 'Unknown' : 'No listing'}
              </span>
            )}
            {!isUnavailable && !offer.exact_model_match && (
              <span className="badge badge-orange">⚠ Variant mismatch</span>
            )}
          </div>
          <ConditionBadge condition={offer.condition} />
        </div>
        <div className="text-right shrink-0">
          {offer.listed_price !== null && offer.listed_price !== undefined ? (
            <>
              <div className="text-2xl font-black text-navy-900">
                {sym}{offer.listed_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              {offer.original_price && (
                <div className="text-xs text-slate-400 line-through">
                  {sym}{offer.original_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              )}
              {offer.headline_discount_pct && (
                <span className="badge badge-green mt-1">−{offer.headline_discount_pct}%</span>
              )}
            </>
          ) : (
            <div className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
              {offer.availability === 'unknown' ? 'Price unknown' : 'Not listed'}
            </div>
          )}
        </div>
      </div>

      {/* Highlight badges */}
      {hasBadge && (
        <div className="flex flex-wrap gap-2 mb-4">
          {isBestDeal && <span className="badge badge-blue">✦ Best verified deal</span>}
          {isCheapest && !isBestDeal && <span className="badge badge-green">↓ Cheapest listed</span>}
          {isHighestRated && <span className="badge badge-teal">★ Highest rated</span>}
          {isBestConditional && (
            <span className="badge badge-yellow" title="Lowest potential price if conditional discount applies — verify eligibility">
              ⚡ Best conditional offer
            </span>
          )}
        </div>
      )}

      {/* Availability / status note */}
      {offer.availability_note && (
        <div className="mb-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
          <strong>ℹ Status:</strong> {offer.availability_note}
        </div>
      )}

      {/* Model mismatch warning */}
      {!offer.exact_model_match && offer.model_match_note && !isUnavailable && (
        <div className="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800 leading-relaxed">
          <strong>⚠ Model warning:</strong> {offer.model_match_note}
        </div>
      )}

      {/* Pricing details */}
      <div className="mb-4">
        <InfoRow
          label="Delivery fee"
          value={
            offer.delivery_fee_unknown || offer.delivery_fee === null ? (
              <span className="text-amber-600 italic">Unknown — verify before buying</span>
            ) : offer.delivery_fee === 0 ? (
              <span className="text-emerald-600 font-bold">Free</span>
            ) : (
              `${sym}${(offer.delivery_fee ?? 0).toFixed(2)}`
            )
          }
        />
        <InfoRow
          label="Comparable total"
          value={
            offer.comparable_total !== null ? (
              <span className="text-navy-900 font-bold">
                {sym}{offer.comparable_total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            ) : (
              <span className="text-amber-600 italic">Unknown (delivery or price not confirmed)</span>
            )
          }
        />
        <InfoRow label="Customer rating" value={<StarRating rating={offer.rating} size="sm" />} />
        <InfoRow
          label="Reviews"
          value={offer.review_count !== null ? offer.review_count.toLocaleString() : '—'}
        />
        <InfoRow
          label="Warranty"
          value={offer.warranty.value ?? <span className="text-slate-400 italic">Not stated</span>}
          verified={offer.warranty.is_verified}
        />
        <InfoRow
          label="Return policy"
          value={offer.return_policy.value ?? <span className="text-slate-400 italic">Not stated</span>}
          verified={offer.return_policy.is_verified}
        />
      </div>

      {/* Conditional discounts */}
      {offer.conditional_discounts.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
            Conditional discounts
          </p>
          {offer.conditional_discounts.map((cd, i) => (
            <div key={i} className="p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-xs mb-2">
              <p className="font-semibold text-yellow-800">{cd.label}</p>
              <p className="text-yellow-700 mt-0.5">{cd.condition_description}</p>
              {!cd.is_verified && (
                <p className="text-amber-600 mt-1 italic">⚠ Condition not verified</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* CTA */}
      {(offer.product_url || offer.retailer_url) && (
        <a
          href={offer.product_url || offer.retailer_url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary w-full text-sm mt-2"
          style={{ textDecoration: 'none' }}
        >
          {offer.product_url ? 'View listing' : `Visit ${offer.retailer_name}`}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </a>
      )}
    </div>
  );
};

export default RetailerCard;
