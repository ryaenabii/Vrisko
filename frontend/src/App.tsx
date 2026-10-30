import React, { useState } from 'react';
import type { ComparisonResult } from './types';
import { compareProducts } from './api';
import Logo from './components/Logo';
import RetailerCard from './components/RetailerCard';
import DealIntegrityScore from './components/DealIntegrityScore';
import CustomerSentiment from './components/CustomerSentiment';
import ComparisonSummaryPanel from './components/ComparisonSummaryPanel';
import EvidencePanel from './components/EvidencePanel';
import LoadingSkeleton from './components/LoadingSkeleton';

// ─── Types ────────────────────────────────────────────────────────────────────

type AppState = 'idle' | 'loading' | 'results' | 'error';

// ─── Sub-components ───────────────────────────────────────────────────────────

const EmptyState: React.FC = () => (
  <div className="flex flex-col items-center justify-center py-20 text-center fade-slide-in">
    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-50 to-teal-50 border border-blue-100 flex items-center justify-center mb-5 shadow-sm">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    </div>
    <h2 className="text-lg font-bold text-navy-900 mb-2">Search for a product to compare</h2>
    <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
      Enter an exact product model number above — for example,{' '}
      <span className="font-mono font-semibold text-blue-600">Sony WH-CH720N</span> — and Vrisko will
      research prices, delivery fees, warranties and customer reviews across multiple retailers.
    </p>
    <div className="mt-8 grid grid-cols-3 gap-6 max-w-sm">
      {[
        { icon: '💰', label: 'Compare prices & delivery' },
        { icon: '🛡️', label: 'Verify warranties & returns' },
        { icon: '⭐', label: 'Analyse customer sentiment' },
      ].map((f) => (
        <div key={f.label} className="flex flex-col items-center gap-2">
          <span className="text-2xl">{f.icon}</span>
          <span className="text-xs text-slate-500 text-center leading-tight">{f.label}</span>
        </div>
      ))}
    </div>
  </div>
);

const ErrorState: React.FC<{ message: string; onRetry: () => void }> = ({ message, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-20 text-center fade-slide-in">
    <div className="w-16 h-16 rounded-full bg-red-50 border border-red-200 flex items-center justify-center mb-4">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    </div>
    <h2 className="text-base font-bold text-navy-900 mb-1">Something went wrong</h2>
    <p className="text-sm text-slate-500 mb-5 max-w-xs">{message}</p>
    <button onClick={onRetry} className="btn-primary text-sm px-5 py-2.5">
      Try again
    </button>
  </div>
);

// ─── Main App ─────────────────────────────────────────────────────────────────

function App() {
  const [query, setQuery] = useState('');
  const [state, setState] = useState<AppState>('idle');
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleCompare = async (q = query) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    setState('loading');
    setResult(null);
    setErrorMsg('');
    try {
      const data = await compareProducts({ query: trimmed, country: 'IN', currency: 'INR', include_used: true });
      setResult(data);
      setState('results');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Unknown error');
      setState('error');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleCompare();
  };

  const handleExampleClick = (model: string) => {
    setQuery(model);
    handleCompare(model);
  };

  // Derived: who is the best deal / cheapest / highest rated
  const bestVerifiedName = result?.summary.best_verified_deal?.retailer_name ?? null;
  const cheapestName = result?.summary.cheapest_listed_price?.retailer_name ?? null;
  const highestRatedName = result?.summary.highest_rated?.retailer_name ?? null;
  const bestConditionalName = result?.summary.best_conditional_offer?.retailer_name ?? null;

  // The checked_at timestamp comes from the first offer (all have the same)
  const checkedAt = result?.offers?.[0]?.checked_at ?? result?.generated_at ?? null;

  return (
    <div className="min-h-screen" style={{ background: 'var(--color-slate-50)' }}>
      {/* ── Top navigation bar ─────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-50 border-b"
        style={{
          background: 'rgba(255,255,255,0.88)',
          backdropFilter: 'blur(12px)',
          borderColor: 'var(--color-slate-200)',
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <Logo />
          <span className="hidden sm:block text-xs text-slate-400 font-medium italic">
            The deal behind the deal.
          </span>
          <div className="flex items-center gap-2">
            <span className="badge badge-teal">🇮🇳 India Market</span>
            <span className="badge badge-blue">
              <span className="pulse-dot w-1.5 h-1.5 rounded-full bg-blue-500 inline-block" />
              API Live
            </span>
          </div>
        </div>
      </header>

      {/* ── Hero search section ────────────────────────────────────────────── */}
      <section
        className="relative overflow-hidden"
        style={{
          background: 'linear-gradient(160deg, #f0f7ff 0%, #f0fdfb 50%, #f8fafc 100%)',
          borderBottom: '1px solid var(--color-slate-200)',
        }}
      >
        {/* Decorative blobs */}
        <div
          className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none"
          style={{
            background: 'radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)',
            transform: 'translate(30%, -30%)',
          }}
        />
        <div
          className="absolute bottom-0 left-0 w-72 h-72 rounded-full pointer-events-none"
          style={{
            background: 'radial-gradient(circle, rgba(13,148,136,0.06) 0%, transparent 70%)',
            transform: 'translate(-30%, 30%)',
          }}
        />

        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 py-14">
          <div className="text-center mb-10">
            <h1 className="text-4xl sm:text-5xl font-black text-navy-900 mb-3 tracking-tight leading-tight">
              Price intelligence,{' '}
              <span className="gradient-text">verified.</span>
            </h1>
            <p className="text-slate-500 text-lg leading-relaxed">
              Enter an exact product model. Vrisko researches retailers, compares real costs and surfaces the deal behind the deal.
            </p>
          </div>

          {/* Search bar */}
          <div className="flex gap-3 flex-col sm:flex-row shadow-lg rounded-2xl overflow-visible">
            <input
              id="product-search"
              type="text"
              className="search-input flex-1 shadow-none"
              placeholder="Search an exact product model..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-label="Product model search"
              disabled={state === 'loading'}
              style={{ borderRadius: '14px' }}
            />
            <button
              id="compare-btn"
              className="btn-primary"
              onClick={() => handleCompare()}
              disabled={state === 'loading' || !query.trim()}
              style={{ borderRadius: '14px' }}
            >
              {state === 'loading' ? (
                <>
                  <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeOpacity="0.3" />
                    <path d="M21 12a9 9 0 00-9-9" strokeLinecap="round" />
                  </svg>
                  Researching…
                </>
              ) : (
                <>
                  Compare Deals
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </div>

          {/* Example chips */}
          <div className="flex items-center gap-2 mt-4 flex-wrap justify-center">
            <span className="text-xs text-slate-400">Try:</span>
            {['Sony WH-CH720N', 'Apple AirPods Pro', 'Samsung Galaxy S24'].map((model) => (
              <button
                key={model}
                onClick={() => handleExampleClick(model)}
                disabled={state === 'loading'}
                className="px-3 py-1 rounded-full text-xs font-semibold bg-white border border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600 transition-all shadow-sm"
              >
                {model}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Results section ────────────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {state === 'idle' && <EmptyState />}
        {state === 'loading' && <LoadingSkeleton />}
        {state === 'error' && (
          <ErrorState message={errorMsg} onRetry={() => setState('idle')} />
        )}

        {state === 'results' && result && (
          <div className="flex flex-col gap-8 fade-slide-in">
            {/* ── DEMO banner ────────────────────────────────────────────── */}
            {result.is_demo && (
              <div className="demo-banner">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#92400e" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <strong>DEMO DATA</strong> — This result uses fictional demo fixtures for UI development.
                Live research via TinyFish will replace this when available.
              </div>
            )}

            {/* ── Product header ─────────────────────────────────────────── */}
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-1">
                Comparison results
              </p>
              <h2 className="text-2xl font-black text-navy-900 tracking-tight">
                {result.product.query}
              </h2>
              <p className="text-sm text-slate-500 mt-0.5">
                {result.offers.length} retailer{result.offers.length !== 1 ? 's' : ''} found •{' '}
                {new Date(result.generated_at).toLocaleString(undefined, {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                })}
              </p>
            </div>

            {/* ── Score + Summary ────────────────────────────────────────── */}
            <div className="grid md:grid-cols-2 gap-6">
              <DealIntegrityScore
                score={result.deal_integrity_score}
                explanation={result.deal_integrity_explanation}
              />
              <ComparisonSummaryPanel summary={result.summary} />
            </div>

            {/* ── Retailer cards ─────────────────────────────────────────── */}
            <div>
              <h2 className="section-heading mb-4">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                  <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
                </svg>
                Retailer Comparison
              </h2>
              <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
                {result.offers.map((offer, i) => (
                  <RetailerCard
                    key={`${offer.retailer_name}-${i}`}
                    offer={offer}
                    rank={i}
                    isBestDeal={offer.retailer_name === bestVerifiedName}
                    isCheapest={offer.retailer_name === cheapestName}
                    isHighestRated={offer.retailer_name === highestRatedName}
                    isBestConditional={offer.retailer_name === bestConditionalName && offer.retailer_name !== bestVerifiedName}
                  />
                ))}
              </div>
            </div>

            {/* ── Sentiment ──────────────────────────────────────────────── */}
            {result.reviews && <CustomerSentiment reviews={result.reviews} />}

            {/* ── Evidence ───────────────────────────────────────────────── */}
            <EvidencePanel items={result.evidence} checkedAt={checkedAt} />
          </div>
        )}
      </main>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer
        className="mt-16 border-t py-8 text-center"
        style={{ borderColor: 'var(--color-slate-200)' }}
      >
        <Logo className="justify-center mb-3" />
        <p className="text-xs text-slate-400">
          Price research for informational purposes only. Always verify prices directly with retailers before purchasing.
        </p>
      </footer>
    </div>
  );
}

export default App;
