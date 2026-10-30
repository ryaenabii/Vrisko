import React from 'react';

interface LogoProps {
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ className = '' }) => (
  <div className={`flex items-center gap-3 ${className}`}>
    {/* V-shaped signal / radar icon */}
    <div className="relative w-10 h-10 flex items-center justify-center">
      <svg viewBox="0 0 40 40" fill="none" className="w-10 h-10">
        <defs>
          <linearGradient id="logoGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#0d9488" />
          </linearGradient>
        </defs>
        <circle cx="20" cy="20" r="19" fill="url(#logoGrad)" opacity="0.12" />
        <path
          d="M8 26 L20 10 L32 26"
          stroke="url(#logoGrad)"
          strokeWidth="2.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <circle cx="20" cy="28" r="3" fill="url(#logoGrad)" />
        <path
          d="M14 22 L20 14 L26 22"
          stroke="url(#logoGrad)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          opacity="0.6"
        />
      </svg>
    </div>
    <div>
      <span className="text-2xl font-black tracking-tight bg-gradient-to-r from-blue-600 to-teal-500 bg-clip-text text-transparent">
        VRISKO
      </span>
    </div>
  </div>
);

export default Logo;
