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
// import WishlistPage from './pages/WishlistPage'; // Uncomment if you create a separate wishlist page
import { Toaster } from 'react-hot-toast'; // <<< IMPORT
// Import Auth Context Hook
import { useAuth } from './contexts/AuthContext';

// --- Protected Route Component ---
// Wraps routes that require authentication.
// Uses the AuthContext to check status.
const ProtectedRoute = ({ children }: { children: JSX.Element }): JSX.Element | null => {
  const { isAuthenticated, isLoading } = useAuth(); // Get auth state and loading status

  if (isLoading) {
    // Display a loading indicator while checking authentication status on initial load
    // This prevents flashing the login page before auth status is confirmed
    return (
        <div className="flex justify-center items-center min-h-[calc(100vh-200px)]"> {/* Adjust height as needed */}
            <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-blue-500 dark:border-blue-400"></div>
        </div>
    );
  }

  if (!isAuthenticated) {
    // If not loading and not authenticated, redirect to the authentication page
    // 'replace' prevents the protected route from being added to browser history
    return <Navigate to="/auth" replace />;
  }
  
  // If authenticated, render the child component (the protected page)
  return children;
};


// --- Main Application Component ---
function App() {
  const { isLoading: isAuthLoading } = useAuth(); // Get loading status for initial check

  return (
    <Router>
      <Toaster position="top-center" reverseOrder={false} /> {/* <<< ADD Toaster */}
      <div className="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-sans"> {/* Added font-sans example */}
        <Navbar /> {/* Render Navbar on all pages */}
        
        <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8"> {/* Responsive padding */}
          {/* Only render routes once initial auth check is done to avoid redirects before confirmation */}
          { !isAuthLoading ? (
            <Routes>
              {/* Public Route: Authentication Page */}
              <Route path="/auth" element={<AuthPage />} />
              
              {/* Protected Routes: Wrap page components with ProtectedRoute */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/stock/:ticker" // Route parameter for the ticker symbol
                element={
                  <ProtectedRoute>
                    <StockDetailPage />
                  </ProtectedRoute>
                } 
              />
              {/* 
              <Route 
                path="/wishlist" // Optional separate wishlist page
                element={
                  <ProtectedRoute>
                    <WishlistPage /> 
                  </ProtectedRoute>
                } 
              /> 
              */}

              {/* Default Route */}
              <Route 
                path="/" 
                element={
                  <ProtectedRoute> 
                    {/* If protected route passes, redirect to dashboard */}
                    <Navigate to="/dashboard" replace />
                  </ProtectedRoute>
                  // If ProtectedRoute redirects (because user is not auth), 
                  // the Navigate below won't be reached, /auth will be shown.
                  // This setup ensures '/' always lands logged-in users on dashboard.
                } 
              />
              
              {/* Fallback for any unmatched routes */}
              <Route path="*" element={<Navigate to="/" replace />} /> 
            </Routes>
          ) : (
             // Display loading spinner centered while initial auth check is happening
             <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
                <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-600 dark:border-blue-500"></div>
            </div>
          )}
        </main>

        <Footer /> {/* Render Footer on all pages */}
      </div>
    </Router>
  );
}

export default App;