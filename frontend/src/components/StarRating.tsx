import React from 'react';

interface StarRatingProps {
  rating: number | null;
  maxStars?: number;
  size?: 'sm' | 'md';
}

const StarRating: React.FC<StarRatingProps> = ({ rating, maxStars = 5, size = 'md' }) => {
  if (rating === null) {
    return <span className="text-xs text-slate-400 italic">No rating</span>;
  }

  const px = size === 'sm' ? 14 : 17;

  return (
    <span className="inline-flex items-center gap-0.5" title={`${rating} / ${maxStars}`}>
      {Array.from({ length: maxStars }).map((_, i) => {
        const fill = Math.min(Math.max(rating - i, 0), 1);
        return (
          <svg key={i} width={px} height={px} viewBox="0 0 24 24">
            <defs>
              <linearGradient id={`star-${i}-${rating}`}>
                <stop offset={`${fill * 100}%`} stopColor="#f59e0b" />
                <stop offset={`${fill * 100}%`} stopColor="#e2e8f0" />
              </linearGradient>
            </defs>
            <path
              fill={`url(#star-${i}-${rating})`}
              d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
            />
          </svg>
        );
      })}
      <span className={`ml-1 font-semibold ${size === 'sm' ? 'text-xs' : 'text-sm'} text-slate-700`}>
        {rating.toFixed(1)}
      </span>
    </span>
  );
};

export default StarRating;
