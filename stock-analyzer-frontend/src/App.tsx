// src/App.tsx
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';
import './styles.css';

// Import Components
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';

// Import Pages
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import StockDetailPage from './pages/StockDetailPage';
import WishlistPage from './pages/WishlistPage'; // <<< UNCOMMENTED
import { Toaster } from 'react-hot-toast';
// Import Auth Context Hook
import { useAuth } from './contexts/AuthContext';

// --- Protected Route Component ---
const ProtectedRoute = ({ children }: { children: JSX.Element }): JSX.Element | null => {
const { isAuthenticated, isLoading } = useAuth();

if (isLoading) {
  return (
      <div className="page-loading-container"> {/* Replaced Tailwind */}
          <div className="page-loader-spinner size-sm"></div> {/* Replaced Tailwind */}
      </div>
  );
}

if (!isAuthenticated) {
  return <Navigate to="/auth" replace />;
}

return children;
};


// --- Main Application Component ---
function App() {
const { isLoading: isAuthLoading } = useAuth();

return (
  <Router>
    <Toaster position="top-center" reverseOrder={false} />
    <div className="app-container"> {/* Replaced Tailwind */}
      <Navbar />
      
      <main className="main-content-area"> {/* Replaced Tailwind */}
        { !isAuthLoading ? (
          <Routes>
            <Route path="/auth" element={<AuthPage />} />
            
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/stock/:ticker"
              element={
                <ProtectedRoute>
                  <StockDetailPage />
                </ProtectedRoute>
              }
            />
            <Route  // <<< ADDED/UNCOMMENTED WishlistPage Route
              path="/wishlist"
              element={
                <ProtectedRoute>
                  <WishlistPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              }
            />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        ) : (
           <div className="page-loading-container"> {/* Replaced Tailwind */}
              <div className="page-loader-spinner size-lg"></div> {/* Replaced Tailwind */}
          </div>
        )}
      </main>

      <Footer />
    </div>
  </Router>
);
}

export default App;