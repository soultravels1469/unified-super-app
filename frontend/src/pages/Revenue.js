import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import RevenueForm from '@/components/RevenueForm';
import { Pencil, Trash2 } from 'lucide-react';

function Revenue() {
  const [revenues, setRevenues] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingRevenue, setEditingRevenue] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRevenues();
  }, []);

  const fetchRevenues = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      setRevenues(response.data);
    } catch (error) {
      toast.error('Failed to load revenues');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this revenue entry?')) return;

    try {
      await axios.delete(`${API}/revenue/${id}`);
      toast.success('Revenue deleted successfully');
      fetchRevenues();
    } catch (error) {
      toast.error('Failed to delete revenue');
    }
  };

  const handleEdit = (revenue) => {
    setEditingRevenue(revenue);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingRevenue(null);
    fetchRevenues();
  };

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container" data-testid="revenue-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="page-title" style={{ margin: 0 }} data-testid="revenue-title">Revenue Tracker</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)} data-testid="add-revenue-button">
          + Add Revenue
        </button>
      </div>

      {showForm && (
        <RevenueForm
          revenue={editingRevenue}
          onClose={handleFormClose}
        />
      )}

      <div className="table-container" data-testid="revenue-table">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Client Name</th>
              <th>Source</th>
              <th>Payment Mode</th>
              <th>Received</th>
              <th>Pending</th>
              <th>Status</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {revenues.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No revenue entries yet. Add your first entry!
                </td>
              </tr>
            ) : (
              revenues.map((rev) => (
                <tr key={rev.id} data-testid={`revenue-row-${rev.id}`}>
                  <td>{rev.date}</td>
                  <td>{rev.client_name}</td>
                  <td>{rev.source}</td>
                  <td>{rev.payment_mode}</td>
                  <td>₹{rev.received_amount.toLocaleString()}</td>
                  <td>₹{rev.pending_amount.toLocaleString()}</td>
                  <td>
                    <span className={`status-badge status-${rev.status.toLowerCase()}`}>
                      {rev.status}
                    </span>
                  </td>
                  <td>{rev.notes || '-'}</td>
                  <td>
                    <div className="actions">
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleEdit(rev)}
                        data-testid={`edit-revenue-${rev.id}`}
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(rev.id)}
                        data-testid={`delete-revenue-${rev.id}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Revenue;
