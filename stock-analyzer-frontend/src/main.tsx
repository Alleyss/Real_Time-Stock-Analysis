// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { AuthProvider } from './contexts/AuthContext.tsx'; // <<< IMPORT

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider> {/* <<< WRAP APP WITH AUTHPROVIDER */}
      <App />
    </AuthProvider>
  </React.StrictMode>
);