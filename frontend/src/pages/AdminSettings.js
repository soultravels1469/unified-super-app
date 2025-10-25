import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Settings, Save } from 'lucide-react';

function AdminSettings() {
  const [settings, setSettings] = useState({
    company_name: '',
    gstin: '',
    logo_url: '',
    bank_name: '',
    account_number: '',
    ifsc_code: '',
    branch: '',
    address: '',
    phone: '',
    email: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`);
      setSettings(response.data);
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setSettings({ ...settings, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      await axios.post(`${API}/admin/settings`, settings);
      toast.success('Settings saved successfully!');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="admin-settings-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <Settings size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Admin Settings</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: '1.5rem', padding: '2rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#1a202c' }}>Company Details</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            <div className="form-group">
              <label>Company Name *</label>
              <input
                type="text"
                name="company_name"
                value={settings.company_name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>GSTIN *</label>
              <input
                type="text"
                name="gstin"
                value={settings.gstin}
                onChange={handleChange}
                placeholder="22AAAAA0000A1Z5"
                required
              />
            </div>

            <div className="form-group">
              <label>Logo URL</label>
              <input
                type="url"
                name="logo_url"
                value={settings.logo_url}
                onChange={handleChange}
                placeholder="https://example.com/logo.png"
              />
            </div>

            <div className="form-group">
              <label>Phone</label>
              <input
                type="tel"
                name="phone"
                value={settings.phone}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={settings.email}
                onChange={handleChange}
              />
            </div>

            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Address</label>
              <textarea
                name="address"
                value={settings.address}
                onChange={handleChange}
                rows="3"
              />
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '2rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#1a202c' }}>Bank Details</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            <div className="form-group">
              <label>Bank Name</label>
              <input
                type="text"
                name="bank_name"
                value={settings.bank_name}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Account Number</label>
              <input
                type="text"
                name="account_number"
                value={settings.account_number}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>IFSC Code</label>
              <input
                type="text"
                name="ifsc_code"
                value={settings.ifsc_code}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Branch</label>
              <input
                type="text"
                name="branch"
                value={settings.branch}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>

        <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn btn-primary" disabled={saving} style={{ padding: '0.875rem 2rem' }}>
            <Save size={18} style={{ marginRight: '0.5rem' }} />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminSettings;
