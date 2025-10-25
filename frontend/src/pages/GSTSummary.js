import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Receipt, Download } from 'lucide-react';

function GSTSummary() {
  const [gstData, setGstData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterDates, setFilterDates] = useState({ start: '', end: '' });

  useEffect(() => {
    fetchGSTData();
  }, []);

  const fetchGSTData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterDates.start && filterDates.end) {
        params.start_date = filterDates.start;
        params.end_date = filterDates.end;
      }
      
      const response = await axios.get(`${API}/accounting/gst-summary`, { params });
      setGstData(response.data);
    } catch (error) {
      toast.error('Failed to load GST data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    if (filterDates.start && filterDates.end) {
      fetchGSTData();
    } else {
      toast.error('Please select both start and end dates');
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="gst-summary-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Receipt size={32} style={{ color: '#f59e0b' }} />
          <h1 className="page-title" style={{ margin: 0 }}>GST Summary</h1>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem', display: 'block' }}>Start Date</label>
            <input
              type="date"
              value={filterDates.start}
              onChange={(e) => setFilterDates({ ...filterDates, start: e.target.value })}
              style={{
                width: '100%',
                padding: '0.625rem',
                borderRadius: '8px',
                border: '2px solid #e2e8f0'
              }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem', display: 'block' }}>End Date</label>
            <input
              type="date"
              value={filterDates.end}
              onChange={(e) => setFilterDates({ ...filterDates, end: e.target.value })}
              style={{
                width: '100%',
                padding: '0.625rem',
                borderRadius: '8px',
                border: '2px solid #e2e8f0'
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button className="btn btn-primary" onClick={handleFilter} style={{ width: '100%' }}>
              Filter
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card" style={{ padding: '1.5rem', background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)' }}>
          <h3 style={{ fontSize: '1rem', color: '#92400e', marginBottom: '1rem' }}>Output GST (Sales)</h3>
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#b45309' }}>CGST</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d97706' }}>₹{gstData?.output_gst.cgst.toLocaleString()}</div>
          </div>
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#b45309' }}>SGST</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d97706' }}>₹{gstData?.output_gst.sgst.toLocaleString()}</div>
          </div>
          <div style={{ borderTop: '2px solid #f59e0b', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#92400e' }}>Total Output GST</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#b45309' }}>₹{gstData?.output_gst.total.toLocaleString()}</div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.5rem', background: 'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)' }}>
          <h3 style={{ fontSize: '1rem', color: '#065f46', marginBottom: '1rem' }}>Input GST (Purchases)</h3>
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#047857' }}>CGST</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#059669' }}>₹{gstData?.input_gst.cgst.toLocaleString()}</div>
          </div>
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#047857' }}>SGST</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#059669' }}>₹{gstData?.input_gst.sgst.toLocaleString()}</div>
          </div>
          <div style={{ borderTop: '2px solid #10b981', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#065f46' }}>Total Input GST</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#047857' }}>₹{gstData?.input_gst.total.toLocaleString()}</div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.5rem', background: 'linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)' }}>
          <h3 style={{ fontSize: '1rem', color: '#831843', marginBottom: '1rem' }}>Net GST Payable</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#be123c', marginTop: '2rem' }}>
            ₹{gstData?.net_gst_payable.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#9f1239', marginTop: '0.5rem' }}>
            (Output GST - Input GST)
          </div>
        </div>
      </div>

      <div className="table-container">
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>GST Records</h3>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Invoice No.</th>
              <th>Client</th>
              <th>Service</th>
              <th>Taxable Amount</th>
              <th>CGST</th>
              <th>SGST</th>
              <th>Total GST</th>
              <th>Total Amount</th>
            </tr>
          </thead>
          <tbody>
            {gstData?.records.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No GST records found
                </td>
              </tr>
            ) : (
              gstData?.records.map((record) => (
                <tr key={record.id}>
                  <td>{record.date}</td>
                  <td style={{ fontWeight: 500, color: '#6366f1' }}>{record.invoice_number}</td>
                  <td>{record.client_name}</td>
                  <td>{record.service_type}</td>
                  <td>₹{record.taxable_amount.toLocaleString()}</td>
                  <td>₹{record.cgst.toLocaleString()}</td>
                  <td>₹{record.sgst.toLocaleString()}</td>
                  <td style={{ fontWeight: 600, color: '#f59e0b' }}>₹{record.total_gst.toLocaleString()}</td>
                  <td style={{ fontWeight: 600 }}>₹{record.total_amount.toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default GSTSummary;
