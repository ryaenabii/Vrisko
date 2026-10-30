import React, { useState } from 'react';
import type { EvidenceItem } from '../types';

interface EvidencePanelProps {
  items: EvidenceItem[];
  checkedAt: string | null;
}

const categoryConfig: Record<
  EvidenceItem['category'],
  { label: string; icon: React.ReactNode; cssClass: string; badge: string }
> = {
  verified: {
    label: 'Verified',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 11 14 15 10" />
      </svg>
    ),
    cssClass: 'evidence-verified',
    badge: 'badge-green',
  },
  conditional: {
    label: 'Conditional',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
    cssClass: 'evidence-conditional',
    badge: 'badge-yellow',
  },
  unknown: {
    label: 'Unknown',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9 9a3 3 0 015.12 2.12c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
    cssClass: 'evidence-unknown',
    badge: 'badge-slate',
  },
  source: {
    label: 'Source',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
      </svg>
    ),
    cssClass: 'evidence-source',
    badge: 'badge-blue',
  },
};

const EvidencePanel: React.FC<EvidencePanelProps> = ({ items, checkedAt }) => {
  const [activeCategory, setActiveCategory] = useState<EvidenceItem['category'] | 'all'>('all');

  const categories = ['all', 'verified', 'conditional', 'unknown', 'source'] as const;
  const filtered = activeCategory === 'all' ? items : items.filter((i) => i.category === activeCategory);
  const counts = {
    all: items.length,
    verified: items.filter((i) => i.category === 'verified').length,
    conditional: items.filter((i) => i.category === 'conditional').length,
    unknown: items.filter((i) => i.category === 'unknown').length,
    source: items.filter((i) => i.category === 'source').length,
  };

  const formatTimestamp = (ts: string) => {
    try {
      return new Date(ts).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="section-heading">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          Evidence
        </h2>
        {checkedAt && (
          <span className="text-xs text-slate-400 font-medium">
            Last checked: {formatTimestamp(checkedAt)}
          </span>
        )}
      </div>

      {/* Category filter tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((cat) => {
          const isActive = activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-navy-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
              style={isActive ? { background: '#0d1526' } : undefined}
            >
              {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)} ({counts[cat]})
            </button>
          );
        })}
      </div>

      {/* Evidence list */}
      <div className="flex flex-col gap-2">
        {filtered.length === 0 && (
          <p className="text-sm text-slate-400 italic text-center py-6">No items in this category.</p>
        )}
        {filtered.map((item, i) => {
          const cfg = categoryConfig[item.category];
          return (
            <div
              key={i}
              className={`${cfg.cssClass} pl-4 pr-3 py-3 rounded-r-xl bg-white border border-l-0 border-slate-100`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 min-w-0">
                  <span className="mt-0.5 shrink-0">{cfg.icon}</span>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-800 leading-snug">{item.label}</p>
                    {item.detail && (
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{item.detail}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`badge ${cfg.badge}`}>{cfg.label}</span>
                  {item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:text-blue-700 transition-colors"
                      title="View source"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
                      </svg>
                    </a>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EvidencePanel;
