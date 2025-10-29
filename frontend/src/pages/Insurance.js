import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Shield } from 'lucide-react';
import RevenueFormEnhanced from '../components/RevenueFormEnhanced';

function Insurance() {
  const [revenues, setRevenues] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingRevenue, setEditingRevenue] = useState(null);

  useEffect(() => {
    fetchRevenues();
  }, []);

  const fetchRevenues = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const insuranceRevenues = response.data.filter(r => r.source === 'Insurance');
      setRevenues(insuranceRevenues);
    } catch (error) {
      toast.error('Failed to load insurance data');
    }
  };

  const handleEdit = (revenue) => {
    setEditingRevenue(revenue);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this insurance entry?')) return;
    try {
      await axios.delete(`${API}/revenue/${id}`);
      toast.success('Insurance entry deleted');
      fetchRevenues();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingRevenue(null);
    fetchRevenues();
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Shield size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Insurance</h1>
        </div>
        <button onClick={() => setShowForm(true)} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={18} />
          Add Insurance
        </button>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Client Name</th>
            <th>Sale Price</th>
            <th>Cost</th>
            <th>Profit</th>
            <th>Received</th>
            <th>Pending</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {revenues.map((revenue) => (
            <tr key={revenue.id}>
              <td>{revenue.date}</td>
              <td>{revenue.client_name}</td>
              <td>₹{(revenue.sale_price || 0).toLocaleString()}</td>
              <td>₹{(revenue.total_cost_price || 0).toLocaleString()}</td>
              <td style={{ color: revenue.profit >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                ₹{(revenue.profit || 0).toLocaleString()}
              </td>
              <td>₹{revenue.received_amount.toLocaleString()}</td>
              <td>₹{revenue.pending_amount.toLocaleString()}</td>
              <td>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  background: revenue.status === 'Received' ? '#d1fae5' : '#fed7aa',
                  color: revenue.status === 'Received' ? '#065f46' : '#9a3412'
                }}>
                  {revenue.status}
                </span>
              </td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={() => handleEdit(revenue)} className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem' }}>
                    <Edit size={14} />
                  </button>
                  <button onClick={() => handleDelete(revenue.id)} className="btn" style={{ padding: '0.25rem 0.75rem', background: '#ef4444', color: 'white' }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {showForm && (
        <RevenueFormEnhanced
          revenue={editingRevenue}
          onClose={handleFormClose}
          defaultSource="Insurance"
        />
      )}
    </div>
  );
}

export default Insurance;
