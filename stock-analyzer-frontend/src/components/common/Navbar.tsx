// src/components/common/Navbar.tsx
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext'; // <<< IMPORT AND USE AUTH CONTEXT

const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth(); // <<< GET VALUES FROM CONTEXT
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <nav className="bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-gray-800 dark:to-black shadow-lg">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div>
            <Link to={isAuthenticated ? "/dashboard" : "/"} className="text-2xl font-bold text-white dark:text-gray-100">
              📊 Stock Analyzer
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {user && <span className="text-gray-300 text-sm hidden md:block">Welcome, {user.username || user.email}!</span>}
                <Link to="/dashboard" className="text-gray-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </Link>
                {/* <Link to="/wishlist" className="text-gray-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Wishlist
                </Link> */}
                <button
                  onClick={handleLogout}
                  className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link to="/auth" className="text-gray-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Login / Sign Up
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;