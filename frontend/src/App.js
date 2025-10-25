import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import '@/App.css';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Revenue from '@/pages/Revenue';
import Expenses from '@/pages/Expenses';
import PendingPayments from '@/pages/PendingPayments';
import Reports from '@/pages/Reports';
import TourPackages from '@/pages/TourPackages';
import Tickets from '@/pages/Tickets';
import Visas from '@/pages/Visas';
import ChartOfAccounts from '@/pages/ChartOfAccounts';
import TrialBalance from '@/pages/TrialBalance';
import CashBankBook from '@/pages/CashBankBook';
import GSTSummary from '@/pages/GSTSummary';
import InvoiceGenerator from '@/pages/InvoiceGenerator';
import Layout from '@/components/Layout';
import { Toaster } from '@/components/ui/sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, username) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
  };

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onLogin={handleLogin} />
              )
            }
          />
          <Route
            path="/*"
            element={
              isAuthenticated ? (
                <Layout onLogout={handleLogout}>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/revenue" element={<Revenue />} />
                    <Route path="/packages" element={<TourPackages />} />
                    <Route path="/tickets" element={<Tickets />} />
                    <Route path="/visas" element={<Visas />} />
                    <Route path="/expenses" element={<Expenses />} />
                    <Route path="/pending" element={<PendingPayments />} />
                    <Route path="/reports" element={<Reports />} />
                  </Routes>
                </Layout>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </div>
  );
}

export default App;
