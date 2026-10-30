import React from 'react';

/** Skeleton loading state for the comparison results section */
const LoadingSkeleton: React.FC = () => (
  <div className="flex flex-col gap-6 mt-8 fade-slide-in">
    {/* Score + summary row */}
    <div className="grid md:grid-cols-2 gap-6">
      <div className="card p-6">
        <div className="shimmer h-4 w-40 mb-5 rounded" />
        <div className="flex gap-6">
          <div className="shimmer w-28 h-28 rounded-full" />
          <div className="flex-1 flex flex-col gap-3">
            <div className="shimmer h-3 w-full rounded" />
            <div className="shimmer h-3 w-4/5 rounded" />
            <div className="shimmer h-3 w-3/5 rounded" />
          </div>
        </div>
      </div>
      <div className="card p-6">
        <div className="shimmer h-4 w-44 mb-5 rounded" />
        <div className="flex flex-col gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl bg-slate-50">
              <div className="shimmer w-8 h-8 rounded-lg" />
              <div className="flex-1 flex flex-col gap-2">
                <div className="shimmer h-3 w-24 rounded" />
                <div className="shimmer h-4 w-40 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>

    {/* Retailer cards */}
    <div>
      <div className="shimmer h-4 w-36 mb-4 rounded" />
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-5">
            <div className="flex justify-between mb-4">
              <div className="flex flex-col gap-2">
                <div className="shimmer h-5 w-28 rounded" />
                <div className="shimmer h-4 w-16 rounded-full" />
              </div>
              <div className="shimmer h-8 w-20 rounded" />
            </div>
            {[1, 2, 3, 4, 5].map((j) => (
              <div key={j} className="flex justify-between py-2 border-b border-slate-100">
                <div className="shimmer h-3 w-20 rounded" />
                <div className="shimmer h-3 w-16 rounded" />
              </div>
            ))}
            <div className="shimmer h-10 w-full rounded-xl mt-4" />
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default LoadingSkeleton;
