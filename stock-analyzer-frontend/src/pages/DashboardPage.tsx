// src/pages/DashboardPage.tsx
import React from 'react';
import SearchBar from '../components/stock/SearchBar';
import WishlistDisplay from '../components/wishlist/WishlistDisplay';

const DashboardPage: React.FC = () => {
  return (
    <div className="dashboard-container"> {/* Centering container for the card */}
      <div className="card dashboard-content-card"> {/* Wider card for dashboard */}
        <h1 className="card-header">Dashboard</h1>
        <div className="card-body">
          <p> {/* Removed mb-4 and text-gray-400, handled by CSS */}
            Search for a stock ticker below or view your wishlist.
          </p>
          
          {/* SearchBar component will be styled via .search-bar-container in CSS */}
          <SearchBar />

          {/* WishlistDisplay component will be styled via .wishlist-container etc. in CSS */}
          {/* mt-4 removed, spacing handled by .wishlist-section-header margin or searchbar margin */}
          <WishlistDisplay />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;