import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [monthlyData, setMonthlyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('yearly');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [summaryRes, monthlyRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/dashboard/monthly`),
      ]);

      setSummary(summaryRes.data);
      setMonthlyData(monthlyRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredData = async () => {
    setLoading(true);
    try {
      let params = {};
      
      if (viewMode === 'monthly' && selectedMonth) {
        const [year, month] = selectedMonth.split('-');
        params = { period: 'month', year: parseInt(year), month: parseInt(month) };
      } else if (viewMode === 'yearly') {
        params = { period: 'year', year: selectedYear };
      }

      const response = await axios.get(`${API}/reports`, { params });
      
      setSummary({
        total_revenue: response.data.total_revenue,
        total_expenses: response.data.total_expenses,
        pending_payments: 0,
        net_profit: response.data.net_profit
      });
    } catch (error) {
      toast.error('Failed to load filtered data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'monthly' && selectedMonth) {
      fetchFilteredData();
    } else if (viewMode === 'yearly') {
      fetchFilteredData();
    }
  }, [viewMode, selectedMonth, selectedYear]);

  const getCurrentMonthDefault = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  };

  useEffect(() => {
    if (viewMode === 'monthly' && !selectedMonth) {
      setSelectedMonth(getCurrentMonthDefault());
    }
  }, [viewMode]);

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container" data-testid="dashboard-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="page-title" style={{ margin: 0 }} data-testid="dashboard-title">Dashboard Overview</h1>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value)}
            style={{
              padding: '0.625rem 1rem',
              borderRadius: '12px',
              border: '2px solid #e2e8f0',
              fontSize: '0.9375rem',
              fontWeight: 500
            }}
            data-testid="view-mode-select"
          >
            <option value="yearly">Yearly View</option>
            <option value="monthly">Monthly View</option>
          </select>

          {viewMode === 'monthly' && (
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              style={{
                padding: '0.625rem 1rem',
                borderRadius: '12px',
                border: '2px solid #e2e8f0',
                fontSize: '0.9375rem'
              }}
              data-testid="month-picker"
            />
          )}

          {viewMode === 'yearly' && (
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              style={{
                padding: '0.625rem 1rem',
                borderRadius: '12px',
                border: '2px solid #e2e8f0',
                fontSize: '0.9375rem'
              }}
              data-testid="year-select"
            >
              {Array.from({ length: 5 }, (_, i) => {
                const y = new Date().getFullYear() - i;
                return <option key={y} value={y}>{y}</option>;
              })}
            </select>
          )}
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card revenue" data-testid="stat-revenue">
          <div className="stat-label">Total Revenue</div>
          <div className="stat-value" data-testid="stat-revenue-value">₹{summary?.total_revenue?.toLocaleString() || 0}</div>
        </div>

        <div className="stat-card expense" data-testid="stat-expenses">
          <div className="stat-label">Total Expenses</div>
          <div className="stat-value" data-testid="stat-expenses-value">₹{summary?.total_expenses?.toLocaleString() || 0}</div>
        </div>

        <div className="stat-card pending" data-testid="stat-pending">
          <div className="stat-label">Pending Payments</div>
          <div className="stat-value" data-testid="stat-pending-value">₹{summary?.pending_payments?.toLocaleString() || 0}</div>
        </div>

        <div className="stat-card profit" data-testid="stat-profit">
          <div className="stat-label">Net Profit</div>
          <div className="stat-value" data-testid="stat-profit-value">₹{summary?.net_profit?.toLocaleString() || 0}</div>
        </div>
      </div>

      {viewMode === 'yearly' && monthlyData.length > 0 && (
        <div className="chart-container" data-testid="monthly-chart">
          <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Monthly Overview</h2>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  background: 'rgba(255, 255, 255, 0.98)',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                }}
              />
              <Legend />
              <Bar dataKey="revenue" fill="#10b981" radius={[8, 8, 0, 0]} />
              <Bar dataKey="expenses" fill="#ef4444" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
