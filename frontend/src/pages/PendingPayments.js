import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { CheckCircle, Edit2 } from 'lucide-react';
import { groupByMonth, getAvailableMonths } from '@/utils/helpers';

function PendingPayments() {
  const [pendingPayments, setPendingPayments] = useState([]);
  const [filteredPayments, setFilteredPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [editingPayment, setEditingPayment] = useState(null);
  const [partialAmount, setPartialAmount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchPendingPayments();
  }, []);

  const fetchPendingPayments = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const pending = response.data.filter((rev) => rev.status === 'Pending' && rev.pending_amount > 0);
      setPendingPayments(pending);
      setFilteredPayments(pending);
    } catch (error) {
      toast.error('Failed to load pending payments');
    } finally {
      setLoading(false);
    }
  };

  // Search filter
  useEffect(() => {
    if (searchTerm) {
      const filtered = pendingPayments.filter(p => 
        p.client_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredPayments(filtered);
    } else {
      setFilteredPayments(pendingPayments);
    }
  }, [searchTerm, pendingPayments]);

  const markAsPaid = async (payment) => {
    try {
      await axios.put(`${API}/revenue/${payment.id}`, {
        status: 'Received',
        received_amount: payment.received_amount + payment.pending_amount,
        pending_amount: 0,
      });
      toast.success('Payment marked as received');
      fetchPendingPayments();
    } catch (error) {
      toast.error('Failed to update payment status');
    }
  };

  const handleEditClick = (payment) => {
    setEditingPayment(payment);
    setPartialAmount(0);
  };

  const handlePartialPayment = async () => {
    if (partialAmount <= 0 || partialAmount > editingPayment.pending_amount) {
      toast.error('Invalid partial payment amount');
      return;
    }

    try {
      const newReceived = editingPayment.received_amount + partialAmount;
      const newPending = editingPayment.pending_amount - partialAmount;
      
      await axios.put(`${API}/revenue/${editingPayment.id}`, {
        received_amount: newReceived,
        pending_amount: newPending,
        status: newPending === 0 ? 'Received' : 'Pending'
      });
      
      toast.success('Partial payment recorded successfully');
      setEditingPayment(null);
      setPartialAmount(0);
      fetchPendingPayments();
    } catch (error) {
      toast.error('Failed to record partial payment');
    }
  };

  const availableMonths = getAvailableMonths(pendingPayments);
  const groupedPayments = groupByMonth(pendingPayments);
  
  const filteredMonths = selectedMonth === 'all' 
    ? Object.entries(groupedPayments)
    : [[selectedMonth, groupedPayments[selectedMonth] || []]];

  const totalPending = pendingPayments.reduce((sum, p) => sum + p.pending_amount, 0);
  const filteredTotal = selectedMonth === 'all'
    ? totalPending
    : (groupedPayments[selectedMonth] || []).reduce((sum, p) => sum + p.pending_amount, 0);

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container" data-testid="pending-payments-page">
      <h1 className="page-title" data-testid="pending-payments-title">Pending Payments</h1>

      <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'linear-gradient(135deg, #fff5e6 0%, #ffe4cc 100%)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.875rem', color: '#92400e', marginBottom: '0.5rem', fontWeight: 500 }}>Total Pending Amount</div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f59e0b' }} data-testid="total-pending-amount">
              ₹{filteredTotal.toLocaleString()}
            </div>
          </div>
          {availableMonths.length > 0 && (
            <div>
              <label style={{ marginRight: '0.75rem', fontWeight: 500, color: '#92400e', fontSize: '0.875rem' }}>Filter:</label>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                style={{
                  padding: '0.625rem 1rem',
                  borderRadius: '12px',
                  border: '2px solid #fbbf24',
                  fontSize: '0.9375rem',
                  minWidth: '180px',
                  background: 'white'
                }}
              >
                <option value="all">All Months</option>
                {availableMonths.map(month => (
                  <option key={month} value={month}>
                    {new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {pendingPayments.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No pending payments. All payments are up to date!
        </div>
      ) : filteredMonths.length === 0 || filteredMonths[0][1]?.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No pending payments for the selected month.
        </div>
      ) : (
        filteredMonths.reverse().map(([month, items]) => (
          items && items.length > 0 && (
            <div key={month} className="month-section">
              <h3 className="month-title">{new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}</h3>
              <div className="table-container" data-testid="pending-payments-table">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Client Name</th>
                      <th>Source</th>
                      <th>Received Amount</th>
                      <th>Pending Amount</th>
                      <th>Notes</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((payment) => (
                      <tr key={payment.id} data-testid={`pending-payment-${payment.id}`}>
                        <td>{payment.date}</td>
                        <td>{payment.client_name}</td>
                        <td>{payment.source}</td>
                        <td>₹{payment.received_amount.toLocaleString()}</td>
                        <td style={{ color: '#f59e0b', fontWeight: 600 }}>
                          ₹{payment.pending_amount.toLocaleString()}
                        </td>
                        <td>{payment.notes || '-'}</td>
                        <td>
                          <div className="actions">
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleEditClick(payment)}
                              data-testid={`edit-payment-${payment.id}`}
                              title="Partial Payment"
                            >
                              <Edit2 size={16} />
                            </button>
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => markAsPaid(payment)}
                              data-testid={`mark-paid-${payment.id}`}
                            >
                              <CheckCircle size={16} style={{ marginRight: '0.5rem' }} />
                              Mark Paid
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        ))
      )}

      {editingPayment && (
        <div className="modal-overlay" onClick={() => setEditingPayment(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>Record Partial Payment</h3>
            
            <div style={{ marginBottom: '1.5rem', padding: '1rem', background: '#f8fafc', borderRadius: '8px' }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Client:</strong> {editingPayment.client_name}
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Total Pending:</strong> ₹{editingPayment.pending_amount.toLocaleString()}
              </div>
              <div>
                <strong>Already Received:</strong> ₹{editingPayment.received_amount.toLocaleString()}
              </div>
            </div>

            <div className="form-group">
              <label>Partial Payment Amount *</label>
              <input
                type="number"
                value={partialAmount}
                onChange={(e) => setPartialAmount(parseFloat(e.target.value) || 0)}
                min="0"
                max={editingPayment.pending_amount}
                step="0.01"
                placeholder="Enter amount received"
                style={{ width: '100%' }}
              />
              <div style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.5rem' }}>
                Remaining after payment: ₹{(editingPayment.pending_amount - partialAmount).toLocaleString()}
              </div>
            </div>

            <div className="form-actions" style={{ marginTop: '2rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setEditingPayment(null)}>
                Cancel
              </button>
              <button type="button" className="btn btn-primary" onClick={handlePartialPayment}>
                Record Payment
              </button>
            </div>
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
              padding: 2rem;
              max-height: 90vh;
              overflow-y: auto;
              box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }

            .form-actions {
              display: flex;
              gap: 1rem;
              justify-content: flex-end;
            }
          `}</style>
        </div>
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
          border-left: 4px solid #f59e0b;
        }
      `}</style>
    </div>
  );
}

export default PendingPayments;
