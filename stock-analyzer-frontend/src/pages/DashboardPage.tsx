// src/pages/DashboardPage.tsx
import React from 'react';
import SearchBar from '../components/stock/SearchBar';
import WishlistDisplay from '../components/wishlist/WishlistDisplay';

const DashboardPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-semibold mb-6">Dashboard</h1>
      <p className="mb-6 text-gray-600 dark:text-gray-400">
        Search for a stock ticker below or view your wishlist.
      </p>
      
      {/* Stock Search Bar */}
      <SearchBar />

      {/* Wishlist Display */}
      <WishlistDisplay />

    </div>
  );
};

export default DashboardPage;