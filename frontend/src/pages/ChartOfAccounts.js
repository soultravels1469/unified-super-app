import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Book } from 'lucide-react';

function ChartOfAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [groupedAccounts, setGroupedAccounts] = useState({});

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/accounting/chart-of-accounts`);
      setAccounts(response.data.accounts);
      
      // Group by type
      const grouped = response.data.accounts.reduce((acc, account) => {
        if (!acc[account.type]) {
          acc[account.type] = [];
        }
        acc[account.type].push(account);
        return acc;
      }, {});
      setGroupedAccounts(grouped);
    } catch (error) {
      toast.error('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="chart-of-accounts-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <Book size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Chart of Accounts</h1>
      </div>

      {Object.entries(groupedAccounts).map(([type, accountList]) => (
        <div key={type} className="account-type-section">
          <h2 className="account-type-title">{type}</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Account Code</th>
                  <th>Account Name</th>
                  <th>Current Balance</th>
                </tr>
              </thead>
              <tbody>
                {accountList.map((account) => (
                  <tr key={account.id}>
                    <td style={{ fontWeight: 500, color: '#6366f1' }}>{account.code}</td>
                    <td>{account.name}</td>
                    <td style={{ fontWeight: 600 }}>
                      ₹{Math.abs(account.balance || 0).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      <style jsx>{`
        .account-type-section {
          margin-bottom: 3rem;
        }

        .account-type-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #1a202c;
          margin-bottom: 1rem;
          padding-bottom: 0.75rem;
          border-bottom: 3px solid #6366f1;
        }
      `}</style>
    </div>
  );
}

export default ChartOfAccounts;
