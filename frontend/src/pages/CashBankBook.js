import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Wallet, Building2 } from 'lucide-react';

function CashBankBook() {
  const [view, setView] = useState('cash'); // cash or bank
  const [entries, setEntries] = useState([]);
  const [balance, setBalance] = useState({ opening: 0, closing: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [view]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const endpoint = view === 'cash' ? '/accounting/cash-book' : '/accounting/bank-book';
      const response = await axios.get(`${API}${endpoint}`);
      setEntries(response.data.entries);
      setBalance({
        opening: response.data.opening_balance,
        closing: response.data.closing_balance
      });
    } catch (error) {
      toast.error(`Failed to load ${view} book`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container" data-testid="cash-bank-book-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {view === 'cash' ? <Wallet size={32} style={{ color: '#10b981' }} /> : <Building2 size={32} style={{ color: '#6366f1' }} />}
          <h1 className="page-title" style={{ margin: 0 }}>{view === 'cash' ? 'Cash' : 'Bank'} Book</h1>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`btn ${view === 'cash' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setView('cash')}
            style={{ padding: '0.75rem 1.5rem' }}
          >
            Cash Book
          </button>
          <button
            className={`btn ${view === 'bank' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setView('bank')}
            style={{ padding: '0.75rem 1.5rem' }}
          >
            Bank Book
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '2rem' }}>
          <div>
            <div style={{ fontSize: '0.875rem', color: '#0369a1', marginBottom: '0.5rem' }}>Current Balance</div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: '#0284c7' }}>
              ₹{balance.closing.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Debit (₹)</th>
                <th>Credit (₹)</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                    No entries yet
                  </td>
                </tr>
              ) : (
                entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.date}</td>
                    <td>{entry.description}</td>
                    <td style={{ color: entry.debit > 0 ? '#059669' : '#94a3b8', fontWeight: 600 }}>
                      {entry.debit > 0 ? entry.debit.toLocaleString() : '-'}
                    </td>
                    <td style={{ color: entry.credit > 0 ? '#dc2626' : '#94a3b8', fontWeight: 600 }}>
                      {entry.credit > 0 ? entry.credit.toLocaleString() : '-'}
                    </td>
                    <td>
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        background: '#f3f4f6',
                        color: '#475569'
                      }}>
                        {entry.reference_type}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default CashBankBook;
