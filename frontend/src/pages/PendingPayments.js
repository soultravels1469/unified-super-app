import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { CheckCircle } from 'lucide-react';

function PendingPayments() {
  const [pendingPayments, setPendingPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingPayments();
  }, []);

  const fetchPendingPayments = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const pending = response.data.filter((rev) => rev.status === 'Pending' && rev.pending_amount > 0);
      setPendingPayments(pending);
    } catch (error) {
      toast.error('Failed to load pending payments');
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container" data-testid="pending-payments-page">
      <h1 className="page-title" data-testid="pending-payments-title">Pending Payments</h1>

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
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {pendingPayments.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No pending payments. All payments are up to date!
                </td>
              </tr>
            ) : (
              pendingPayments.map((payment) => (
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
                    <button
                      className="btn btn-success btn-sm"
                      onClick={() => markAsPaid(payment)}
                      data-testid={`mark-paid-${payment.id}`}
                    >
                      <CheckCircle size={16} style={{ marginRight: '0.5rem' }} />
                      Mark Paid
                    </button>
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

export default PendingPayments;
