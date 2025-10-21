import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import RevenueForm from '@/components/RevenueForm';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth } from '@/utils/helpers';

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
    if (!window.confirm('Are you sure you want to delete this visa entry?')) return;
    try {
      await axios.delete(`${API}/revenue/${id}`);
      toast.success('Visa entry deleted successfully');
      fetchVisas();
    } catch (error) {
      toast.error('Failed to delete visa entry');
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
        <h1 className="page-title" style={{ margin: 0 }}>Visas</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)} data-testid="add-visa-button">
          + Add Visa
        </button>
      </div>

      {showForm && (
        <RevenueForm
          revenue={editingVisa}
          onClose={handleFormClose}
          defaultSource="Visa"
        />
      )}

      {Object.keys(groupedVisas).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No visa entries yet. Add your first visa!
        </div>
      ) : (
        Object.entries(groupedVisas).reverse().map(([month, items]) => (
          <div key={month} className="month-section" data-testid={`month-${month}`}>
            <h3 className="month-title">{new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Client Name</th>
                    <th>Payment Mode</th>
                    <th>Received</th>
                    <th>Pending</th>
                    <th>Status</th>
                    <th>Supplier</th>
                    <th>Notes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((visa) => (
                    <tr key={visa.id}>
                      <td>{visa.date}</td>
                      <td>{visa.client_name}</td>
                      <td>{visa.payment_mode}</td>
                      <td>₹{visa.received_amount.toLocaleString()}</td>
                      <td>₹{visa.pending_amount.toLocaleString()}</td>
                      <td>
                        <span className={`status-badge status-${visa.status.toLowerCase()}`}>
                          {visa.status}
                        </span>
                      </td>
                      <td>{visa.supplier || '-'}</td>
                      <td>{visa.notes || '-'}</td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(visa)}>
                            <Pencil size={16} />
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(visa.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}

      <style jsx>{`
        .month-section {
          margin-bottom: 2.5rem;
        }

        .month-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #1a202c;
          margin-bottom: 1rem;
          padding-left: 0.5rem;
          border-left: 4px solid #6366f1;
        }
      `}</style>
    </div>
  );
}

export default Visas;
