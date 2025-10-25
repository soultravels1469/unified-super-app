import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { X } from 'lucide-react';

function ExpenseForm({ expense, onClose }) {
  const [formData, setFormData] = useState({
    date: '',
    category: '',
    payment_mode: 'Cash',
    amount: 0,
    description: '',
    purchase_type: 'General Expense',
    supplier_gstin: '',
    invoice_number: '',
    gst_rate: 0
  });

  useEffect(() => {
    if (expense) {
      setFormData(expense);
    }
  }, [expense]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (expense) {
        await axios.put(`${API}/expenses/${expense.id}`, formData);
        toast.success('Expense updated successfully');
      } else {
        await axios.post(`${API}/expenses`, formData);
        toast.success('Expense added successfully');
      }
      onClose();
    } catch (error) {
      toast.error('Failed to save expense');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'amount' ? parseFloat(value) || 0 : value,
    }));
  };

  return (
    <div className="modal-overlay" data-testid="expense-form-modal">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{expense ? 'Edit Expense' : 'Add Expense'}</h2>
          <button className="close-btn" onClick={onClose} data-testid="close-expense-form-button">
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
                data-testid="expense-date-input"
              />
            </div>

            <div className="form-group">
              <label>Category *</label>
              <input
                type="text"
                name="category"
                value={formData.category}
                onChange={handleChange}
                placeholder="e.g., Office Rent, Salaries, Travel"
                required
                data-testid="expense-category-input"
              />
            </div>

            <div className="form-group">
              <label>Payment Mode *</label>
              <select name="payment_mode" value={formData.payment_mode} onChange={handleChange} data-testid="expense-payment-select">
                <option value="Cash">Cash</option>
                <option value="UPI">UPI</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="Card">Card</option>
                <option value="Cheque">Cheque</option>
              </select>
            </div>

            <div className="form-group">
              <label>Amount *</label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                min="0"
                step="0.01"
                required
                data-testid="expense-amount-input"
              />
            </div>

            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="3"
                placeholder="Additional details about this expense"
                data-testid="expense-description-input"
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" data-testid="submit-expense-button">
              {expense ? 'Update' : 'Add'} Expense
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
          max-width: 700px;
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

export default ExpenseForm;
