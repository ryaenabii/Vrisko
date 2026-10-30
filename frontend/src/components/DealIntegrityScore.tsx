import React, { useEffect, useState } from 'react';

interface DealIntegrityScoreProps {
  score: number | null;
  explanation: string | null;
}

const ScoreRing: React.FC<{ score: number }> = ({ score }) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius; // ~283
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';

  const label =
    score >= 75 ? 'High integrity' : score >= 50 ? 'Moderate' : 'Low integrity';

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle
            cx="50" cy="50" r={radius}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth="10"
          />
          <circle
            cx="50" cy="50" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.34,1.56,0.64,1)' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-black" style={{ color }}>{score}</span>
          <span className="text-xs font-bold text-slate-500">/ 100</span>
        </div>
      </div>
      <span className="text-xs font-semibold" style={{ color }}>{label}</span>
    </div>
  );
};

const DealIntegrityScore: React.FC<DealIntegrityScoreProps> = ({ score, explanation }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    if (score === null) return;
    const timer = setTimeout(() => setAnimatedScore(score), 100);
    return () => clearTimeout(timer);
  }, [score]);

  if (score === null) return null;

  return (
    <div className="card p-6">
      <h2 className="section-heading mb-5">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        Deal Integrity Score
      </h2>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        <ScoreRing score={animatedScore} />
        <div className="flex-1">
          <p className="text-sm text-slate-600 leading-relaxed">{explanation}</p>
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            {[
              { label: '75–100', desc: 'High', color: '#22c55e', bg: '#dcfce7' },
              { label: '50–74', desc: 'Moderate', color: '#f59e0b', bg: '#fef9c3' },
              { label: '0–49', desc: 'Low', color: '#ef4444', bg: '#fee2e2' },
            ].map((tier) => (
              <div
                key={tier.desc}
                className="rounded-xl p-2"
                style={{ background: tier.bg }}
              >
                <div className="text-xs font-bold" style={{ color: tier.color }}>{tier.desc}</div>
                <div className="text-xs text-slate-500 mt-0.5">{tier.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DealIntegrityScore;
