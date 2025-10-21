import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';

function Reports() {
  const [reportData, setReportData] = useState(null);
  const [period, setPeriod] = useState('month');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [loading, setLoading] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const params = { period };
      if (period === 'month') {
        params.year = year;
        params.month = month;
      } else if (period === 'year') {
        params.year = year;
      }

      const response = await axios.get(`${API}/reports`, { params });
      setReportData(response.data);
    } catch (error) {
      toast.error('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  return (
    <div className="page-container" data-testid="reports-page">
      <h1 className="page-title" data-testid="reports-title">Reports</h1>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Period</label>
            <select value={period} onChange={(e) => setPeriod(e.target.value)} data-testid="period-select">
              <option value="month">Monthly</option>
              <option value="year">Yearly</option>
            </select>
          </div>

          {period === 'month' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Month</label>
              <select value={month} onChange={(e) => setMonth(Number(e.target.value))} data-testid="month-select">
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Year</label>
            <select value={year} onChange={(e) => setYear(Number(e.target.value))} data-testid="year-select">
              {Array.from({ length: 5 }, (_, i) => {
                const y = new Date().getFullYear() - i;
                return (
                  <option key={y} value={y}>
                    {y}
                  </option>
                );
              })}
            </select>
          </div>
        </div>

        <button className="btn btn-primary" onClick={fetchReport} disabled={loading} data-testid="generate-report-button">
          {loading ? 'Generating...' : 'Generate Report'}
        </button>
      </div>

      {reportData && (
        <>
          <div className="stats-grid" data-testid="report-summary">
            <div className="stat-card revenue">
              <div className="stat-label">Total Revenue</div>
              <div className="stat-value">₹{reportData.total_revenue.toLocaleString()}</div>
            </div>

            <div className="stat-card expense">
              <div className="stat-label">Total Expenses</div>
              <div className="stat-value">₹{reportData.total_expenses.toLocaleString()}</div>
            </div>

            <div className="stat-card profit">
              <div className="stat-label">Net Profit</div>
              <div className="stat-value">₹{reportData.net_profit.toLocaleString()}</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
            <div className="card" data-testid="revenue-by-source">
              <h3 style={{ marginBottom: '1rem', fontSize: '1.125rem', fontWeight: 600 }}>Revenue by Source</h3>
              {Object.keys(reportData.revenue_by_source).length === 0 ? (
                <p style={{ color: '#94a3b8' }}>No revenue data available</p>
              ) : (
                <div>
                  {Object.entries(reportData.revenue_by_source).map(([source, amount]) => (
                    <div key={source} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f1f3f5' }}>
                      <span style={{ color: '#475569' }}>{source}</span>
                      <span style={{ fontWeight: 600, color: '#10b981' }}>₹{amount.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card" data-testid="expenses-by-category">
              <h3 style={{ marginBottom: '1rem', fontSize: '1.125rem', fontWeight: 600 }}>Expenses by Category</h3>
              {Object.keys(reportData.expense_by_category).length === 0 ? (
                <p style={{ color: '#94a3b8' }}>No expense data available</p>
              ) : (
                <div>
                  {Object.entries(reportData.expense_by_category).map(([category, amount]) => (
                    <div key={category} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f1f3f5' }}>
                      <span style={{ color: '#475569' }}>{category}</span>
                      <span style={{ fontWeight: 600, color: '#ef4444' }}>₹{amount.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Reports;
