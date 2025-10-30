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
import Insurance from '@/pages/Insurance';
import ChartOfAccounts from '@/pages/ChartOfAccounts';
import TrialBalance from '@/pages/TrialBalance';
import CashBankBook from '@/pages/CashBankBook';
import GSTSummary from '@/pages/GSTSummary';
import InvoiceGenerator from '@/pages/InvoiceGenerator';
import AdminSettings from '@/pages/AdminSettings';
import UserManagement from '@/pages/UserManagement';
import DataManagement from '@/pages/DataManagement';
import BankAccounts from '@/pages/BankAccounts';
import Vendors from '@/pages/Vendors';
import ActivityLogs from '@/pages/ActivityLogs';
import VendorReport from '@/pages/VendorReport';
import VendorPayments from '@/pages/VendorPayments';
import CRMDashboard from '@/pages/crm/CRMDashboard';
import Leads from '@/pages/crm/Leads';
import LeadDetail from '@/pages/crm/LeadDetail';
import UpcomingTravel from '@/pages/crm/UpcomingTravel';
import Reminders from '@/pages/crm/Reminders';
import CRMReports from '@/pages/crm/Reports';
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

  const handleLogin = (token, username, role) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('role', role);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
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
                    <Route path="/insurance" element={<Insurance />} />
                    <Route path="/expenses" element={<Expenses />} />
                    <Route path="/pending" element={<PendingPayments />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/crm/dashboard" element={<CRMDashboard />} />
                    <Route path="/crm/leads" element={<Leads />} />
                    <Route path="/crm/leads/:leadId" element={<LeadDetail />} />
                    <Route path="/crm/upcoming" element={<UpcomingTravel />} />
                    <Route path="/crm/reminders" element={<Reminders />} />
                    <Route path="/crm/reports" element={<CRMReports />} />
                    <Route path="/accounting/chart-of-accounts" element={<ChartOfAccounts />} />
                    <Route path="/accounting/trial-balance" element={<TrialBalance />} />
                    <Route path="/accounting/cash-bank" element={<CashBankBook />} />
                    <Route path="/accounting/gst" element={<GSTSummary />} />
                    <Route path="/accounting/invoices" element={<InvoiceGenerator />} />
                    <Route path="/accounting/bank-accounts" element={<BankAccounts />} />
                    <Route path="/accounting/vendors" element={<Vendors />} />
                    <Route path="/accounting/vendor-report" element={<VendorReport />} />
                    <Route path="/admin/settings" element={<AdminSettings />} />
                    <Route path="/admin/users" element={<UserManagement />} />
                    <Route path="/admin/data" element={<DataManagement />} />
                    <Route path="/admin/logs" element={<ActivityLogs />} />
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
