import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import RevenueForm from '@/components/RevenueForm';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth } from '@/utils/helpers';

function TourPackages() {
  const [packages, setPackages] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingPackage, setEditingPackage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const filtered = response.data.filter(r => r.source === 'Package');
      setPackages(filtered);
    } catch (error) {
      toast.error('Failed to load tour packages');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this package?')) return;
    try {
      await axios.delete(`${API}/revenue/${id}`);
      toast.success('Package deleted successfully');
      fetchPackages();
    } catch (error) {
      toast.error('Failed to delete package');
    }
  };

  const handleEdit = (pkg) => {
    setEditingPackage(pkg);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingPackage(null);
    fetchPackages();
  };

  const groupedPackages = groupByMonth(packages);

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="packages-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>Tour Packages</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.5rem' }}>
            ℹ️ Entries are auto-generated from the Revenue module
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)} data-testid="add-package-button">
          + Add Package
        </button>
      </div>

      {showForm && (
        <RevenueForm
          revenue={editingPackage}
          onClose={handleFormClose}
          defaultSource="Package"
        />
      )}

      {Object.keys(groupedPackages).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No tour packages yet. Add your first package!
        </div>
      ) : (
        Object.entries(groupedPackages).reverse().map(([month, items]) => (
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
                  {items.map((pkg) => (
                    <tr key={pkg.id}>
                      <td>{pkg.date}</td>
                      <td>{pkg.client_name}</td>
                      <td>{pkg.payment_mode}</td>
                      <td>₹{pkg.received_amount.toLocaleString()}</td>
                      <td>₹{pkg.pending_amount.toLocaleString()}</td>
                      <td>
                        <span className={`status-badge status-${pkg.status.toLowerCase()}`}>
                          {pkg.status}
                        </span>
                      </td>
                      <td>{pkg.supplier || '-'}</td>
                      <td>{pkg.notes || '-'}</td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(pkg)}>
                            <Pencil size={16} />
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(pkg.id)}>
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

export default TourPackages;
