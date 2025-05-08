// src/components/common/Navbar.tsx
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
// Example icon import (install react-icons: npm install react-icons)
import { FiLogOut, FiLogIn, FiUserPlus, FiGrid, FiHeart } from 'react-icons/fi';

const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  // Define styles using theme colors
  const navBg = 'bg-gradient-to-r from-brand-dark via-brand-dark-secondary to-brand-dark'; // Dark gradient always
  const textColor = 'text-brand-text-light';
  const hoverTextColor = 'hover:text-white';
  const linkStyle = `${textColor} ${hoverTextColor} px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ease-in-out flex items-center space-x-1`;
  const brandAccent = 'text-[var(--accent-secondary)]'; // Lime in dark mode

  return (
    // Use custom dark gradient, maybe add a border
    <nav className={`${navBg} shadow-lg border-b border-gray-700/50`}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16"> {/* Fixed height */}
          {/* Logo / Brand Name */}
          <div className="flex-shrink-0">
            <Link to={isAuthenticated ? "/dashboard" : "/"} className="text-2xl font-bold text-white flex items-center">
              <span className={`mr-2 ${brandAccent}`}>📊</span> Stock Analyzer
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex md:items-center md:space-x-4">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className={linkStyle}>
                  <FiGrid className="mr-1"/> Dashboard
                </Link>
                <Link to="/wishlist" className={linkStyle}> {/* Assuming you have a wishlist page/route */}
                  <FiHeart className="mr-1"/> Wishlist
                </Link>
                {/* Add other links here */}
              </>
            ) : null /* No main nav links when logged out */}
          </div>

          {/* Right Side: Auth actions / User Info */}
          <div className="flex items-center">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                 <span className={`${textColor} text-sm hidden lg:block`}>
                   Welcome, {user?.username || user?.email}!
                 </span>
                 <button
                   onClick={handleLogout}
                   title="Logout"
                   // Use ghost variant for icon-like button
                   className={`bg-transparent ${textColor} hover:bg-red-600/20 hover:text-red-400 p-2 rounded-md transition-colors duration-150 ease-in-out`}
                 >
                   <FiLogOut size={18} />
                 </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                 <Link to="/auth?view=login" className={linkStyle}> {/* Assuming AuthPage handles query param */}
                    <FiLogIn className="mr-1"/> Login
                 </Link>
                 <Link to="/auth?view=signup" className={`${linkStyle} bg-brand-accent-lime/10 text-brand-accent-lime px-3 py-1.5 rounded-md hover:bg-brand-accent-lime/20 hover:text-brand-accent-lime`}>
                    <FiUserPlus className="mr-1"/> Sign Up
                 </Link>
              </div>
            )}
             {/* Optional: Dark Mode Toggle */}
             {/* <button className="...">...</button> */}
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;