// src/components/common/Button.tsx
import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
}

const Button: React.FC<ButtonProps> = ({ children, isLoading, variant = 'primary', className, ...rest }) => {
  const baseStyle = "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2";
  
  let variantStyle = "";
  switch (variant) {
    case 'secondary':
      variantStyle = "bg-gray-600 hover:bg-gray-700 focus:ring-gray-500 dark:bg-gray-500 dark:hover:bg-gray-600";
      break;
    case 'danger':
      variantStyle = "bg-red-600 hover:bg-red-700 focus:ring-red-500";
      break;
    case 'primary':
    default:
      variantStyle = "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600";
      break;
  }

  return (
    <button
      className={`${baseStyle} ${variantStyle} ${isLoading ? 'opacity-75 cursor-not-allowed' : ''} ${className}`}
      disabled={isLoading}
      {...rest}
    >
      {isLoading ? (
        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : (
        children
      )}
    </button>
  );
};

export default Button;