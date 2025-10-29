import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Building2 } from 'lucide-react';

function BankAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [formData, setFormData] = useState({
    bank_name: '',
    account_number: '',
    ifsc_code: '',
    holder_name: '',
    account_type: 'Savings'
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/bank-accounts`);
      setAccounts(response.data);
    } catch (error) {
      toast.error('Failed to load bank accounts');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingAccount) {
        await axios.put(`${API}/bank-accounts/${editingAccount.id}`, formData);
        toast.success('Bank account updated');
      } else {
        await axios.post(`${API}/bank-accounts`, formData);
        toast.success('Bank account added');
      }
      setShowForm(false);
      setEditingAccount(null);
      setFormData({ bank_name: '', account_number: '', ifsc_code: '', holder_name: '', account_type: 'Savings' });
      fetchAccounts();
    } catch (error) {
      toast.error('Failed to save bank account');
    }
  };

  const handleEdit = (account) => {
    setEditingAccount(account);
    setFormData(account);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this bank account?')) return;
    try {
      await axios.delete(`${API}/bank-accounts/${id}`);
      toast.success('Bank account deleted');
      fetchAccounts();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Building2 size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Bank Accounts</h1>
        </div>
        <button onClick={() => { setShowForm(true); setEditingAccount(null); setFormData({ bank_name: '', account_number: '', ifsc_code: '', holder_name: '', account_type: 'Savings' }); }} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={18} />
          Add Bank Account
        </button>
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        {accounts.map((account) => (
          <div key={account.id} className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>{account.bank_name}</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem', color: '#64748b' }}>
                  <div><strong>Account Holder:</strong> {account.holder_name}</div>
                  <div><strong>Account No:</strong> {account.account_number}</div>
                  <div><strong>IFSC:</strong> {account.ifsc_code}</div>
                  <div><strong>Type:</strong> {account.account_type}</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => handleEdit(account)} className="btn btn-secondary" style={{ padding: '0.5rem', minWidth: 'auto' }}>
                  <Edit size={16} />
                </button>
                <button onClick={() => handleDelete(account.id)} className="btn" style={{ padding: '0.5rem', minWidth: 'auto', background: '#ef4444', color: 'white' }}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card" style={{ width: '90%', maxWidth: '600px', padding: '2rem' }}>
            <h2 style={{ marginBottom: '1.5rem' }}>{editingAccount ? 'Edit' : 'Add'} Bank Account</h2>
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div className="form-group">
                  <label>Bank Name *</label>
                  <input type="text" value={formData.bank_name} onChange={(e) => setFormData({...formData, bank_name: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Account Holder Name *</label>
                  <input type="text" value={formData.holder_name} onChange={(e) => setFormData({...formData, holder_name: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Account Number *</label>
                  <input type="text" value={formData.account_number} onChange={(e) => setFormData({...formData, account_number: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>IFSC Code *</label>
                  <input type="text" value={formData.ifsc_code} onChange={(e) => setFormData({...formData, ifsc_code: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Account Type *</label>
                  <select value={formData.account_type} onChange={(e) => setFormData({...formData, account_type: e.target.value})} required>
                    <option value="Savings">Savings</option>
                    <option value="Current">Current</option>
                  </select>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => { setShowForm(false); setEditingAccount(null); }} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default BankAccounts;