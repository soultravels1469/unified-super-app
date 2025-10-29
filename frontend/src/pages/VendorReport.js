import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function VendorReport() {
  const [report, setReport] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    try {
      const response = await axios.get(`${API}/reports/vendor-business`);
      setReport(response.data);
    } catch (error) {
      toast.error('Failed to load vendor report');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="page-container">Loading report...</div>;

  const totalBusiness = report.reduce((sum, v) => sum + v.total_business, 0);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <TrendingUp size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Vendor Business Report</h1>
      </div>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Total Business with Vendors</h3>
        <div style={{ fontSize: '2rem', fontWeight: 700, color: '#6366f1' }}>₹{totalBusiness.toLocaleString()}</div>
      </div>

      {report.length > 0 ? (
        <>
          <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Business Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={report}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="vendor_name" />
                <YAxis />
                <Tooltip formatter={(value) => `₹${value.toLocaleString()}`} />
                <Legend />
                <Bar dataKey="total_business" fill="#6366f1" name="Total Business" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Vendor Details</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Vendor Name</th>
                  <th>Total Business</th>
                  <th>Transactions</th>
                  <th>Avg per Transaction</th>
                </tr>
              </thead>
              <tbody>
                {report.map((vendor, index) => (
                  <tr key={index}>
                    <td>{vendor.vendor_name}</td>
                    <td style={{ fontWeight: 600 }}>₹{vendor.total_business.toLocaleString()}</td>
                    <td>{vendor.transaction_count}</td>
                    <td>₹{(vendor.total_business / vendor.transaction_count).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No vendor business data available yet
        </div>
      )}
    </div>
  );
}

export default VendorReport;