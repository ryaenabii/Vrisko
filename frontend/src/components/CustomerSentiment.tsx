import React from 'react';
import type { CustomerReviews } from '../types';
import StarRating from './StarRating';

const sentimentConfig = {
  positive: { label: 'Positive', bg: '#dcfce7', color: '#15803d', icon: '😊' },
  mixed: { label: 'Mixed', bg: '#fef9c3', color: '#854d0e', icon: '😐' },
  negative: { label: 'Negative', bg: '#fee2e2', color: '#991b1b', icon: '😟' },
  insufficient_data: { label: 'Insufficient data', bg: '#f1f5f9', color: '#475569', icon: '📊' },
};

interface CustomerSentimentProps {
  reviews: CustomerReviews;
}

const CustomerSentiment: React.FC<CustomerSentimentProps> = ({ reviews }) => {
  const config = sentimentConfig[reviews.sentiment];

  return (
    <div className="card p-6">
      <h2 className="section-heading mb-5">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
        </svg>
        Customer Sentiment
      </h2>

      {/* Overview row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-5">
        <div className="rounded-xl p-4 bg-slate-50 flex flex-col gap-1">
          <span className="text-xs text-slate-500 font-medium">Average rating</span>
          <StarRating rating={reviews.average_rating} />
        </div>
        <div className="rounded-xl p-4 bg-slate-50 flex flex-col gap-1">
          <span className="text-xs text-slate-500 font-medium">Total reviews</span>
          <span className="text-lg font-black text-navy-900">
            {reviews.total_review_count.toLocaleString()}
          </span>
        </div>
        <div
          className="rounded-xl p-4 col-span-2 sm:col-span-1 flex flex-col gap-1"
          style={{ background: config.bg }}
        >
          <span className="text-xs font-medium" style={{ color: config.color }}>Overall sentiment</span>
          <span className="text-lg font-bold flex items-center gap-2" style={{ color: config.color }}>
            {config.icon} {config.label}
          </span>
          {reviews.sentiment_confidence !== null && (
            <span className="text-xs" style={{ color: config.color }}>
              {Math.round(reviews.sentiment_confidence * 100)}% confidence
            </span>
          )}
        </div>
      </div>

      {/* Feedback */}
      <div className="grid sm:grid-cols-2 gap-4">
        {reviews.positive_feedback && (
          <div className="rounded-xl p-4 bg-emerald-50 border border-emerald-100">
            <p className="text-xs font-bold text-emerald-700 mb-2 flex items-center gap-1">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z" />
                <path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />
              </svg>
              What customers like
            </p>
            <p className="text-xs text-slate-700 leading-relaxed">{reviews.positive_feedback}</p>
          </div>
        )}
        {reviews.negative_feedback && (
          <div className="rounded-xl p-4 bg-red-50 border border-red-100">
            <p className="text-xs font-bold text-red-700 mb-2 flex items-center gap-1">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z" />
                <path d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />
              </svg>
              Common complaints
            </p>
            <p className="text-xs text-slate-700 leading-relaxed">{reviews.negative_feedback}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerSentiment;
