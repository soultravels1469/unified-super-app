import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';
import { TrendingUp, TrendingDown, DollarSign, CreditCard, Clock, PieChart as PieChartIcon } from 'lucide-react';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [monthlyData, setMonthlyData] = useState([]);
  const [expenseByCategory, setExpenseByCategory] = useState([]);
  const [revenueBySource, setRevenueBySource] = useState([]);
  const [cashFlow, setCashFlow] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('yearly');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [dateFilter, setDateFilter] = useState({ start: '', end: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [summaryRes, monthlyRes, expensesRes, revenuesRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/dashboard/monthly`),
        axios.get(`${API}/expenses`),
        axios.get(`${API}/revenue`)
      ]);

      setSummary(summaryRes.data);
      setMonthlyData(monthlyRes.data);
      
      // Process expense by category
      const expenseCategories = {};
      expensesRes.data.forEach(exp => {
        const cat = exp.category || 'Other';
        expenseCategories[cat] = (expenseCategories[cat] || 0) + exp.amount;
      });
      const expensePieData = Object.entries(expenseCategories).map(([name, value]) => ({ name, value }));
      setExpenseByCategory(expensePieData);

      // Process revenue by source
      const revenueSources = {};
      revenuesRes.data.forEach(rev => {
        if (rev.status === 'Received') {
          const source = rev.source || 'Other';
          revenueSources[source] = (revenueSources[source] || 0) + rev.received_amount;
        }
      });
      const revenuePieData = Object.entries(revenueSources).map(([name, value]) => ({ name, value }));
      setRevenueBySource(revenuePieData);

      // Calculate cash flow (monthly net profit)
      const cashFlowData = monthlyRes.data.map(m => ({
        month: m.month,
        profit: m.revenue - m.expenses
      }));
      setCashFlow(cashFlowData);

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

  const profitMargin = summary ? ((summary.net_profit / summary.total_revenue) * 100).toFixed(1) : 0;

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container" data-testid="dashboard-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="page-title" style={{ margin: 0 }} data-testid="dashboard-title">Business Dashboard</h1>
        
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Total Revenue</div>
              <div className="stat-value" data-testid="stat-revenue-value">₹{summary?.total_revenue?.toLocaleString() || 0}</div>
            </div>
            <DollarSign size={40} style={{ color: '#10b981', opacity: 0.3 }} />
          </div>
        </div>

        <div className="stat-card expense" data-testid="stat-expenses">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Total Expenses</div>
              <div className="stat-value" data-testid="stat-expenses-value">₹{summary?.total_expenses?.toLocaleString() || 0}</div>
            </div>
            <CreditCard size={40} style={{ color: '#ef4444', opacity: 0.3 }} />
          </div>
        </div>

        <div className="stat-card pending" data-testid="stat-pending">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Pending Payments</div>
              <div className="stat-value" data-testid="stat-pending-value">₹{summary?.pending_payments?.toLocaleString() || 0}</div>
            </div>
            <Clock size={40} style={{ color: '#f59e0b', opacity: 0.3 }} />
          </div>
        </div>

        <div className="stat-card profit" data-testid="stat-profit">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Net Profit</div>
              <div className="stat-value" data-testid="stat-profit-value">₹{summary?.net_profit?.toLocaleString() || 0}</div>
              <div style={{ fontSize: '0.875rem', color: summary?.net_profit >= 0 ? '#10b981' : '#ef4444', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                {summary?.net_profit >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {profitMargin}% Margin
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
        {viewMode === 'yearly' && monthlyData.length > 0 && (
          <div className="chart-container" data-testid="revenue-expense-chart">
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Revenue vs Expenses Trend</h2>
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
                <Bar dataKey="revenue" fill="#10b981" radius={[8, 8, 0, 0]} name="Revenue" />
                <Bar dataKey="expenses" fill="#ef4444" radius={[8, 8, 0, 0]} name="Expenses" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {cashFlow.length > 0 && (
          <div className="chart-container" data-testid="profit-loss-chart">
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Profit/Loss Trend</h2>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={cashFlow}>
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
                <Line type="monotone" dataKey="profit" stroke="#6366f1" strokeWidth={3} name="Net Profit" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
        {expenseByCategory.length > 0 && (
          <div className="chart-container" data-testid="expense-breakdown-chart">
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Expense Breakdown by Category</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={expenseByCategory}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {expenseByCategory.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {revenueBySource.length > 0 && (
          <div className="chart-container" data-testid="revenue-source-chart">
            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Revenue by Source</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={revenueBySource}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {revenueBySource.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
