import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth } from '@/utils/helpers';
import RevenueFormEnhanced from '../components/RevenueFormEnhanced';

function Visas() {
  const [visas, setVisas] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingVisa, setEditingVisa] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVisas();
  }, []);

  const fetchVisas = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const filtered = response.data.filter(r => r.source === 'Visa');
      setVisas(filtered);
    } catch (error) {
      toast.error('Failed to load visas');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this visa?')) return;
    try {
      await axios.delete(`${API}/revenue/${id}`);
      toast.success('Visa deleted successfully');
      fetchVisas();
    } catch (error) {
      toast.error('Failed to delete visa');
    }
  };

  const handleEdit = (visa) => {
    setEditingVisa(visa);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingVisa(null);
    fetchVisas();
  };

  const groupedVisas = groupByMonth(visas);

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="visas-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>Visas</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.5rem' }}>
            ℹ️ Entries are auto-generated from the Revenue module
          </p>
        </div>
      </div>

      {showForm && (
        <RevenueFormEnhanced
          revenue={editingVisa}
          onClose={handleFormClose}
          defaultSource="Visa"
        />
      )}

      {Object.keys(groupedVisas).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No visas yet. Visas are created automatically through the Revenue module.
        </div>
      ) : (
        Object.entries(groupedVisas).reverse().map(([month, items]) => (
          <div key={month} className="month-section" data-testid={`month-${month}`}>
            <h2 className="month-title">{month}</h2>
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
                {items.map((visa) => (
                  <tr key={visa.id}>
                    <td>{visa.date}</td>
                    <td>{visa.client_name}</td>
                    <td>₹{(visa.sale_price || 0).toLocaleString()}</td>
                    <td>₹{(visa.total_cost_price || 0).toLocaleString()}</td>
                    <td style={{ color: visa.profit >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      ₹{(visa.profit || 0).toLocaleString()}
                    </td>
                    <td>₹{visa.received_amount.toLocaleString()}</td>
                    <td>₹{visa.pending_amount.toLocaleString()}</td>
                    <td>
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        borderRadius: '9999px',
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        background: visa.status === 'Completed' ? '#d1fae5' : '#fed7aa',
                        color: visa.status === 'Completed' ? '#065f46' : '#9a3412'
                      }}>
                        {visa.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleEdit(visa)}
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.75rem' }}
                          data-testid={`edit-visa-${visa.id}`}
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(visa.id)}
                          className="btn"
                          style={{ padding: '0.25rem 0.75rem', background: '#ef4444', color: 'white' }}
                          data-testid={`delete-visa-${visa.id}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}

export default Visas;