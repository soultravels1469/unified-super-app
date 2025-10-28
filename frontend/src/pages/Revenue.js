import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import RevenueFormEnhanced from '../components/RevenueFormEnhanced';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth } from '@/utils/helpers';

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

  const groupedRevenues = groupByMonth(revenues);

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
        <RevenueFormEnhanced
          revenue={editingRevenue}
          onClose={handleFormClose}
        />
      )}

      {Object.keys(groupedRevenues).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No revenue entries yet. Add your first entry!
        </div>
      ) : (
        Object.entries(groupedRevenues).reverse().map(([month, items]) => (
          <div key={month} className="month-section" data-testid={`month-${month}`}>
            <h3 className="month-title">{new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}</h3>
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
                    <th>Supplier</th>
                    <th>Notes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((rev) => (
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
                      <td>{rev.supplier || '-'}</td>
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

export default Revenue;
