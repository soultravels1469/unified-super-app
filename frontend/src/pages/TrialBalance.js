import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Scale } from 'lucide-react';

function TrialBalance() {
  const [trialBalance, setTrialBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrialBalance();
  }, []);

  const fetchTrialBalance = async () => {
    try {
      const response = await axios.get(`${API}/accounting/trial-balance`);
      setTrialBalance(response.data);
    } catch (error) {
      toast.error('Failed to load trial balance');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="trial-balance-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <Scale size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Trial Balance</h1>
      </div>

      {trialBalance?.balanced === false && (
        <div className="alert-warning" style={{ marginBottom: '2rem', padding: '1rem', background: '#fef3c7', border: '2px solid #f59e0b', borderRadius: '12px' }}>
          <strong>Warning:</strong> Trial balance is not balanced! Total debits and credits must be equal.
        </div>
      )}

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Account Code</th>
              <th>Account Name</th>
              <th>Account Type</th>
              <th>Debit (₹)</th>
              <th>Credit (₹)</th>
            </tr>
          </thead>
          <tbody>
            {trialBalance?.accounts?.map((account) => (
              <tr key={account.account_code}>
                <td style={{ fontWeight: 500, color: '#6366f1' }}>{account.account_code}</td>
                <td>{account.account_name}</td>
                <td>
                  <span style={{
                    padding: '0.25rem 0.75rem',
                    borderRadius: '12px',
                    fontSize: '0.875rem',
                    background: account.account_type === 'Assets' || account.account_type === 'Expenses' ? '#dbeafe' : '#d1fae5',
                    color: account.account_type === 'Assets' || account.account_type === 'Expenses' ? '#1e40af' : '#065f46'
                  }}>
                    {account.account_type}
                  </span>
                </td>
                <td style={{ fontWeight: 600, color: account.debit > 0 ? '#059669' : '#94a3b8' }}>
                  {account.debit > 0 ? account.debit.toLocaleString() : '-'}
                </td>
                <td style={{ fontWeight: 600, color: account.credit > 0 ? '#dc2626' : '#94a3b8' }}>
                  {account.credit > 0 ? account.credit.toLocaleString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot style={{ background: '#f8fafc', fontWeight: 700, fontSize: '1.1rem' }}>
            <tr>
              <td colSpan="3" style={{ textAlign: 'right', padding: '1.5rem' }}>Total:</td>
              <td style={{ color: '#059669' }}>₹{trialBalance?.total_debit?.toLocaleString()}</td>
              <td style={{ color: '#dc2626' }}>₹{trialBalance?.total_credit?.toLocaleString()}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="card" style={{ marginTop: '2rem', padding: '1.5rem', background: trialBalance?.balanced ? '#d1fae5' : '#fef3c7' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '1.125rem', fontWeight: 600 }}>Status:</span>
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: trialBalance?.balanced ? '#065f46' : '#92400e' }}>
            {trialBalance?.balanced ? '✓ Balanced' : '✗ Not Balanced'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default TrialBalance;
