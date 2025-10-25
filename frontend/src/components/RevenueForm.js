import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { X } from 'lucide-react';

function RevenueForm({ revenue, onClose, defaultSource = '' }) {
  const [formData, setFormData] = useState({
    date: '',
    client_name: '',
    source: defaultSource || 'Visa',
    payment_mode: 'Cash',
    total_amount: 0,
    pending_amount: 0,
    received_amount: 0,
    status: 'Pending',
    supplier: '',
    notes: '',
  });

  useEffect(() => {
    if (revenue) {
      // Calculate total from existing data
      const total = (revenue.received_amount || 0) + (revenue.pending_amount || 0);
      setFormData({ ...revenue, total_amount: total });
    } else if (defaultSource) {
      setFormData(prev => ({ ...prev, source: defaultSource }));
    }
  }, [revenue, defaultSource]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (revenue) {
        await axios.put(`${API}/revenue/${revenue.id}`, formData);
        toast.success('Revenue updated successfully');
      } else {
        await axios.post(`${API}/revenue`, formData);
        toast.success('Revenue added successfully');
      }
      onClose();
    } catch (error) {
      toast.error('Failed to save revenue');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name.includes('amount') ? parseFloat(value) || 0 : value,
    }));
  };

  return (
    <div className="modal-overlay" data-testid="revenue-form-modal">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{revenue ? 'Edit Revenue' : 'Add Revenue'}</h2>
          <button className="close-btn" onClick={onClose} data-testid="close-form-button">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label>Date *</label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
                data-testid="revenue-date-input"
              />
            </div>

            <div className="form-group">
              <label>Client Name *</label>
              <input
                type="text"
                name="client_name"
                value={formData.client_name}
                onChange={handleChange}
                required
                data-testid="revenue-client-input"
              />
            </div>

            <div className="form-group">
              <label>Source *</label>
              <select 
                name="source" 
                value={formData.source} 
                onChange={handleChange} 
                data-testid="revenue-source-select"
                disabled={!!defaultSource}
              >
                <option value="Visa">Visa</option>
                <option value="Ticket">Ticket</option>
                <option value="Package">Package</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Payment Mode *</label>
              <select name="payment_mode" value={formData.payment_mode} onChange={handleChange} data-testid="revenue-payment-select">
                <option value="Cash">Cash</option>
                <option value="UPI">UPI</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="Card">Card</option>
                <option value="Cheque">Cheque</option>
              </select>
            </div>

            <div className="form-group">
              <label>Received Amount *</label>
              <input
                type="number"
                name="received_amount"
                value={formData.received_amount}
                onChange={handleChange}
                min="0"
                step="0.01"
                required
                data-testid="revenue-received-input"
              />
            </div>

            <div className="form-group">
              <label>Pending Amount *</label>
              <input
                type="number"
                name="pending_amount"
                value={formData.pending_amount}
                onChange={handleChange}
                min="0"
                step="0.01"
                required
                data-testid="revenue-pending-input"
              />
            </div>

            <div className="form-group">
              <label>Status *</label>
              <select name="status" value={formData.status} onChange={handleChange} data-testid="revenue-status-select">
                <option value="Pending">Pending</option>
                <option value="Received">Received</option>
              </select>
            </div>

            <div className="form-group">
              <label>Supplier</label>
              <input
                type="text"
                name="supplier"
                value={formData.supplier}
                onChange={handleChange}
                placeholder="Hotel, airline, or land supplier"
                data-testid="revenue-supplier-input"
              />
            </div>

            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows="3"
                data-testid="revenue-notes-input"
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" data-testid="submit-revenue-button">
              {revenue ? 'Update' : 'Add'} Revenue
            </button>
          </div>
        </form>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 1rem;
        }

        .modal-content {
          background: white;
          border-radius: 20px;
          max-width: 800px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 2rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .modal-header h2 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #1a202c;
        }

        .close-btn {
          background: none;
          border: none;
          cursor: pointer;
          color: #64748b;
          padding: 0.5rem;
          border-radius: 8px;
          transition: background 0.2s ease;
        }

        .close-btn:hover {
          background: #f1f5f9;
        }

        form {
          padding: 2rem;
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1.5rem;
        }

        .form-actions {
          display: flex;
          gap: 1rem;
          justify-content: flex-end;
          margin-top: 2rem;
        }

        @media (max-width: 768px) {
          .form-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

export default RevenueForm;
