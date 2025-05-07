// src/components/common/LoadingSpinner.tsx
import React from 'react';

interface LoadingSpinnerProps {
    size?: string; // e.g., 'h-8 w-8'
    text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'h-10 w-10', text }) => {
  return (
    <div className="flex flex-col items-center justify-center space-y-2">
        <div className={`animate-spin rounded-full border-t-4 border-b-4 border-blue-500 dark:border-blue-400 ${size}`}></div>
        {text && <p className="text-sm text-gray-500 dark:text-gray-400">{text}</p>}
    </div>
  );
};

export default LoadingSpinner;