import { useState } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Download, Upload, Trash2, RefreshCw } from 'lucide-react';
import { exportToExcel, exportToCSV } from '@/utils/export';

function DataManagement() {
  const [loading, setLoading] = useState(false);
  const role = localStorage.getItem('role');

  if (role !== 'admin') {
    return (
      <div className="page-container">
        <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
          <h2>Access Denied</h2>
          <p>Only administrators can access this page.</p>
        </div>
      </div>
    );
  }

  const handleExport = async (type) => {
    setLoading(true);
    try {
      let data, filename;
      
      switch(type) {
        case 'revenue':
          const revRes = await axios.get(`${API}/revenue`);
          data = revRes.data.map(r => ({
            Date: r.date,
            Client: r.client_name,
            Source: r.source,
            'Payment Mode': r.payment_mode,
            'Received Amount': r.received_amount,
            'Pending Amount': r.pending_amount,
            Status: r.status,
            Supplier: r.supplier || '',
            Notes: r.notes || ''
          }));
          filename = 'Revenue_Export';
          break;
          
        case 'expenses':
          const expRes = await axios.get(`${API}/expenses`);
          data = expRes.data.map(e => ({
            Date: e.date,
            Category: e.category,
            'Payment Mode': e.payment_mode,
            Amount: e.amount,
            'Purchase Type': e.purchase_type || '',
            Description: e.description || ''
          }));
          filename = 'Expenses_Export';
          break;
          
        case 'ledger':
          const ledgerRes = await axios.get(`${API}/accounting/ledger`);
          data = ledgerRes.data.entries.map(l => ({
            Date: l.date,
            Account: l.account,
            'Account Type': l.account_type,
            Debit: l.debit,
            Credit: l.credit,
            Description: l.description
          }));
          filename = 'Ledger_Export';
          break;
          
        case 'trial-balance':
          const tbRes = await axios.get(`${API}/accounting/trial-balance`);
          data = tbRes.data.accounts.map(a => ({
            'Account Code': a.account_code,
            'Account Name': a.account_name,
            'Account Type': a.account_type,
            Debit: a.debit,
            Credit: a.credit,
            Balance: a.balance
          }));
          filename = 'Trial_Balance_Export';
          break;
          
        case 'gst':
          const gstRes = await axios.get(`${API}/accounting/gst-summary`);
          data = gstRes.data.records.map(g => ({
            Date: g.date,
            Type: g.type,
            'Invoice Number': g.invoice_number || '',
            'Client/Supplier': g.client_name || g.category || '',
            'Taxable Amount': g.taxable_amount,
            CGST: g.cgst,
            SGST: g.sgst,
            'Total GST': g.total_gst,
            'Total Amount': g.total_amount
          }));
          filename = 'GST_Records_Export';
          break;
      }
      
      exportToExcel(data, filename);
      toast.success(`${filename} exported successfully!`);
    } catch (error) {
      toast.error('Failed to export data');
    } finally {
      setLoading(false);
    }
  };

  const handleClearTestData = async () => {
    if (!window.confirm('Are you sure you want to clear all accounting test data? This will delete ledgers and GST records.')) {
      return;
    }
    
    setLoading(true);
    try {
      await axios.delete(`${API}/admin/clear-test-data`);
      toast.success('Test data cleared successfully!');
    } catch (error) {
      toast.error('Failed to clear test data');
    } finally {
      setLoading(false);
    }
  };

  const handleRebuildAccounting = async () => {
    if (!window.confirm('This will rebuild all accounting entries from revenue and expense data. Continue?')) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/rebuild-accounting`);
      toast.success(`Accounting rebuilt! Processed ${response.data.revenues_processed} revenues and ${response.data.expenses_processed} expenses.`);
    } catch (error) {
      toast.error('Failed to rebuild accounting data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <h1 className="page-title">Data Management & Export</h1>

      <div className="card" style={{ marginBottom: '2rem', padding: '2rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>Export Data</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <button className="btn btn-primary" onClick={() => handleExport('revenue')} disabled={loading}>
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Export Revenue
          </button>
          <button className="btn btn-primary" onClick={() => handleExport('expenses')} disabled={loading}>
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Export Expenses
          </button>
          <button className="btn btn-primary" onClick={() => handleExport('ledger')} disabled={loading}>
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Export Ledger
          </button>
          <button className="btn btn-primary" onClick={() => handleExport('trial-balance')} disabled={loading}>
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Export Trial Balance
          </button>
          <button className="btn btn-primary" onClick={() => handleExport('gst')} disabled={loading}>
            <Download size={16} style={{ marginRight: '0.5rem' }} />
            Export GST Records
          </button>
        </div>
        <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#64748b' }}>
          All exports are in Excel (.xlsx) format with current date in filename
        </div>
      </div>

      <div className="card" style={{ padding: '2rem', background: '#fef3c7', border: '2px solid #f59e0b' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#92400e' }}>Admin Utilities</h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'white', borderRadius: '12px' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Clear Test Data</div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Remove all ledgers, GST records, and reset account balances</div>
            </div>
            <button className="btn btn-danger" onClick={handleClearTestData} disabled={loading}>
              <Trash2 size={16} style={{ marginRight: '0.5rem' }} />
              Clear Test Data
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'white', borderRadius: '12px' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Rebuild Accounting Data</div>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Recreate all accounting entries from existing revenue & expense data</div>
            </div>
            <button className="btn btn-secondary" onClick={handleRebuildAccounting} disabled={loading}>
              <RefreshCw size={16} style={{ marginRight: '0.5rem' }} />
              Rebuild
            </button>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: '2rem', padding: '1.5rem', background: '#eff6ff' }}>
        <div style={{ fontSize: '0.875rem', color: '#1e40af' }}>
          <strong>Note:</strong> Export functionality creates Excel files with current date. Rebuild feature will recreate all accounting entries from scratch based on your revenue and expense data.
        </div>
      </div>
    </div>
  );
}

export default DataManagement;
