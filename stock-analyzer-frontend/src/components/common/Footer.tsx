// src/components/common/Footer.tsx
import React from 'react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="bg-gray-200 dark:bg-gray-800 text-center py-4 shadow-inner">
      <div className="container mx-auto">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          © {currentYear} Stock Analyzer. All rights reserved.
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
          Disclaimer: For informational purposes only. Not financial advice.
        </p>
      </div>
    </footer>
  );
};

export default Footer;