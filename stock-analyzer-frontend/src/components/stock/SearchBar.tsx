// src/components/stock/SearchBar.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Input from '../common/Input';
import Button from '../common/Button';

const SearchBar: React.FC = () => {
  const [ticker, setTicker] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (ticker.trim()) {
      navigate(`/stock/${ticker.trim().toUpperCase()}`); // Navigate to detail page
      setTicker(''); // Clear input after search
    }
  };

  return (
    <form onSubmit={handleSearch} className="flex items-end space-x-2 mb-6">
      <div className="flex-grow">
        <Input
          label="Search Stock Ticker"
          name="tickerSearch"
          placeholder="e.g., AAPL, MSFT"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="mb-0" // Remove default bottom margin from Input component
        />
      </div>
      <Button type="submit" variant="primary" className="w-auto px-6 h-[42px]"> {/* Adjust height to match input */}
        Search
      </Button>
    </form>
  );
};

export default SearchBar;