// src/components/common/Input.tsx
import React from 'react';

// ... (interface definition same as before) ...

const Input: React.FC<InputProps> = ({ label, name, error, className = '', ...rest }) => {
  return (
    <div className={`mb-4 ${className}`}> {/* Allow passing className to container */}
      {label && (
        <label htmlFor={name} className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
          {label}
        </label>
      )}
      <input
        id={name}
        name={name}
        // Use CSS variables, refine focus styles with neon accent
        className={`
          w-full px-3 py-2 border rounded-md shadow-sm
          bg-[var(--bg-secondary)] border-[var(--border-color)] text-[var(--text-primary)]
          placeholder:text-[var(--text-muted)]
          focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
          sm:text-sm transition-colors duration-150 ease-in-out
          ${error ? 'border-red-500 focus:ring-red-500' : ''}
        `}
        {...rest}
      />
      {error && <p className="mt-1 text-xs text-red-500 dark:text-red-400">{error}</p>}
    </div>
  );
};

export default Input;