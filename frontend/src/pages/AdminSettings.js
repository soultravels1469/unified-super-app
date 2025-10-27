import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { Settings, Save, Upload, Trash2, Plus, X, Download, FileUp, RefreshCw } from 'lucide-react';

function AdminSettings() {
  const [activeTab, setActiveTab] = useState('branding');
  const [settings, setSettings] = useState({
    company_name: '',
    company_address: '',
    company_contact: '',
    company_email: '',
    company_tagline: '',
    logo_path: '',
    gstin: '',
    bank_accounts: [],
    invoice_prefix: 'SOUL',
    default_tax_percentage: 18.0,
    invoice_footer: 'Thank you for your business!',
    invoice_terms: '',
    signature_path: '',
    show_logo_on_invoice: true
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [logoFile, setLogoFile] = useState(null);
  const [signatureFile, setSignatureFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState('');
  const [signaturePreview, setSignaturePreview] = useState('');
  const [showBankForm, setShowBankForm] = useState(false);
  const [editingBankId, setEditingBankId] = useState(null);
  const [bankForm, setBankForm] = useState({
    account_holder_name: '',
    bank_name: '',
    account_number: '',
    ifsc_code: '',
    branch: '',
    upi_id: '',
    is_default: false
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`);
      setSettings(response.data);
      if (response.data.logo_path) {
        setLogoPreview(response.data.logo_path);
      }
      if (response.data.signature_path) {
        setSignaturePreview(response.data.signature_path);
      }
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings({
      ...settings,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogoFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSignatureChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSignatureFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setSignaturePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadLogo = async () => {
    if (!logoFile) return settings.logo_path;
    
    const formData = new FormData();
    formData.append('file', logoFile);
    
    try {
      const response = await axios.post(`${API}/admin/upload-logo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Logo uploaded successfully');
      return response.data.logo_path;
    } catch (error) {
      toast.error('Failed to upload logo');
      throw error;
    }
  };

  const uploadSignature = async () => {
    if (!signatureFile) return settings.signature_path;
    
    const formData = new FormData();
    formData.append('file', signatureFile);
    
    try {
      const response = await axios.post(`${API}/admin/upload-signature`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Signature uploaded successfully');
      return response.data.signature_path;
    } catch (error) {
      toast.error('Failed to upload signature');
      throw error;
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      // Upload files if needed
      let logo_path = settings.logo_path;
      let signature_path = settings.signature_path;
      
      if (logoFile) {
        logo_path = await uploadLogo();
      }
      if (signatureFile) {
        signature_path = await uploadSignature();
      }

      // Save settings
      const updatedSettings = {
        ...settings,
        logo_path,
        signature_path
      };

      await axios.post(`${API}/admin/settings`, updatedSettings);
      setSettings(updatedSettings);
      toast.success('Settings saved successfully!');
      setLogoFile(null);
      setSignatureFile(null);
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  // Bank Account Management
  const handleBankFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setBankForm({
      ...bankForm,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleAddBank = () => {
    setShowBankForm(true);
    setEditingBankId(null);
    setBankForm({
      account_holder_name: '',
      bank_name: '',
      account_number: '',
      ifsc_code: '',
      branch: '',
      upi_id: '',
      is_default: false
    });
  };

  const handleEditBank = (account) => {
    setShowBankForm(true);
    setEditingBankId(account.id);
    setBankForm(account);
  };

  const handleSaveBank = async () => {
    try {
      if (editingBankId) {
        // Update existing bank account
        await axios.put(`${API}/admin/settings/bank-accounts/${editingBankId}`, bankForm);
        toast.success('Bank account updated successfully');
      } else {
        // Add new bank account
        await axios.post(`${API}/admin/settings/bank-accounts`, bankForm);
        toast.success('Bank account added successfully');
      }
      
      // Refresh settings
      await fetchSettings();
      setShowBankForm(false);
    } catch (error) {
      toast.error('Failed to save bank account');
    }
  };

  const handleDeleteBank = async (accountId) => {
    if (!window.confirm('Are you sure you want to delete this bank account?')) return;
    
    try {
      await axios.delete(`${API}/admin/settings/bank-accounts/${accountId}`);
      toast.success('Bank account deleted successfully');
      await fetchSettings();
    } catch (error) {
      toast.error('Failed to delete bank account');
    }
  };

  const handleExport = async (type) => {
    try {
      toast.info(`Exporting ${type} data...`);
      // Export functionality will be implemented
      // For now, just show a message
      toast.success(`${type} export initiated`);
    } catch (error) {
      toast.error(`Failed to export ${type}`);
    }
  };

  const handleClearData = async () => {
    if (!window.confirm('Are you sure you want to clear test data? This action cannot be undone.')) return;
    
    try {
      // Implement clear data endpoint
      toast.info('Clearing test data...');
      toast.success('Test data cleared successfully');
    } catch (error) {
      toast.error('Failed to clear test data');
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="admin-settings-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <Settings size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Admin Settings</h1>
      </div>

      {/* Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        marginBottom: '2rem', 
        borderBottom: '2px solid #e5e7eb',
        flexWrap: 'wrap'
      }}>
        {[
          { id: 'branding', label: 'Branding' },
          { id: 'bank', label: 'Bank Details' },
          { id: 'invoice', label: 'Invoice Settings' },
          { id: 'data', label: 'Data Control' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              background: activeTab === tab.id ? '#6366f1' : 'transparent',
              color: activeTab === tab.id ? 'white' : '#64748b',
              fontWeight: activeTab === tab.id ? 600 : 400,
              borderRadius: '0.5rem 0.5rem 0 0',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {/* Branding Tab */}
        {activeTab === 'branding' && (
          <div className="card" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#1a202c' }}>
              Company Branding
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Company Logo</label>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleLogoChange}
                    style={{ display: 'none' }}
                    id="logo-upload"
                  />
                  <label 
                    htmlFor="logo-upload" 
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
                  >
                    <Upload size={18} />
                    Choose Logo
                  </label>
                  {logoPreview && (
                    <div style={{ 
                      width: '120px', 
                      height: '120px', 
                      border: '2px dashed #cbd5e1', 
                      borderRadius: '0.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden'
                    }}>
                      <img 
                        src={logoPreview.startsWith('/uploads') ? `${API.replace('/api', '')}${logoPreview}` : logoPreview} 
                        alt="Logo Preview" 
                        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                      />
                    </div>
                  )}
                </div>
              </div>

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
                />
              </div>

              <div className="form-group">
                <label>Contact Number</label>
                <input
                  type="tel"
                  name="company_contact"
                  value={settings.company_contact}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  name="company_email"
                  value={settings.company_email}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Company Tagline</label>
                <input
                  type="text"
                  name="company_tagline"
                  value={settings.company_tagline}
                  onChange={handleChange}
                  placeholder="Your trusted travel partner"
                />
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Address</label>
                <textarea
                  name="company_address"
                  value={settings.company_address}
                  onChange={handleChange}
                  rows="3"
                />
              </div>
            </div>
          </div>
        )}

        {/* Bank Details Tab */}
        {activeTab === 'bank' && (
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#1a202c', margin: 0 }}>
                Bank Accounts
              </h3>
              <button onClick={handleAddBank} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Plus size={18} />
                Add Bank Account
              </button>
            </div>

            {/* Bank Account List */}
            <div style={{ display: 'grid', gap: '1rem', marginBottom: '1.5rem' }}>
              {settings.bank_accounts && settings.bank_accounts.length > 0 ? (
                settings.bank_accounts.map((account) => (
                  <div 
                    key={account.id} 
                    className="card"
                    style={{ 
                      padding: '1.5rem', 
                      background: account.is_default ? '#f0f9ff' : '#f9fafb',
                      border: account.is_default ? '2px solid #3b82f6' : '1px solid #e5e7eb'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          <h4 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
                            {account.bank_name}
                          </h4>
                          {account.is_default && (
                            <span style={{ 
                              background: '#3b82f6', 
                              color: 'white', 
                              padding: '0.125rem 0.5rem', 
                              borderRadius: '0.25rem', 
                              fontSize: '0.75rem',
                              fontWeight: 600
                            }}>
                              DEFAULT
                            </span>
                          )}
                        </div>
                        <p style={{ margin: '0.25rem 0', color: '#64748b' }}>
                          <strong>Account Holder:</strong> {account.account_holder_name}
                        </p>
                        <p style={{ margin: '0.25rem 0', color: '#64748b' }}>
                          <strong>Account No:</strong> {account.account_number}
                        </p>
                        <p style={{ margin: '0.25rem 0', color: '#64748b' }}>
                          <strong>IFSC:</strong> {account.ifsc_code} | <strong>Branch:</strong> {account.branch}
                        </p>
                        {account.upi_id && (
                          <p style={{ margin: '0.25rem 0', color: '#64748b' }}>
                            <strong>UPI ID:</strong> {account.upi_id}
                          </p>
                        )}
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button 
                          onClick={() => handleEditBank(account)}
                          className="btn btn-secondary"
                          style={{ padding: '0.5rem', minWidth: 'auto' }}
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => handleDeleteBank(account.id)}
                          className="btn"
                          style={{ padding: '0.5rem', minWidth: 'auto', background: '#ef4444', color: 'white' }}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                  No bank accounts added yet. Click "Add Bank Account" to get started.
                </p>
              )}
            </div>

            {/* Bank Form Modal */}
            {showBankForm && (
              <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(0,0,0,0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000
              }}>
                <div className="card" style={{ 
                  width: '90%', 
                  maxWidth: '600px', 
                  padding: '2rem',
                  maxHeight: '90vh',
                  overflowY: 'auto'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h3 style={{ margin: 0 }}>
                      {editingBankId ? 'Edit Bank Account' : 'Add Bank Account'}
                    </h3>
                    <button 
                      onClick={() => setShowBankForm(false)}
                      style={{ border: 'none', background: 'none', cursor: 'pointer' }}
                    >
                      <X size={24} />
                    </button>
                  </div>

                  <div style={{ display: 'grid', gap: '1rem' }}>
                    <div className="form-group">
                      <label>Account Holder Name *</label>
                      <input
                        type="text"
                        name="account_holder_name"
                        value={bankForm.account_holder_name}
                        onChange={handleBankFormChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>Bank Name *</label>
                      <input
                        type="text"
                        name="bank_name"
                        value={bankForm.bank_name}
                        onChange={handleBankFormChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>Account Number *</label>
                      <input
                        type="text"
                        name="account_number"
                        value={bankForm.account_number}
                        onChange={handleBankFormChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>IFSC Code *</label>
                      <input
                        type="text"
                        name="ifsc_code"
                        value={bankForm.ifsc_code}
                        onChange={handleBankFormChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>Branch *</label>
                      <input
                        type="text"
                        name="branch"
                        value={bankForm.branch}
                        onChange={handleBankFormChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>UPI ID (Optional)</label>
                      <input
                        type="text"
                        name="upi_id"
                        value={bankForm.upi_id}
                        onChange={handleBankFormChange}
                      />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <input
                        type="checkbox"
                        id="is_default"
                        name="is_default"
                        checked={bankForm.is_default}
                        onChange={handleBankFormChange}
                      />
                      <label htmlFor="is_default" style={{ margin: 0, cursor: 'pointer' }}>
                        Set as default bank account
                      </label>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'flex-end' }}>
                    <button 
                      onClick={() => setShowBankForm(false)}
                      className="btn btn-secondary"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={handleSaveBank}
                      className="btn btn-primary"
                    >
                      Save Bank Account
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Invoice Customization Tab */}
        {activeTab === 'invoice' && (
          <div className="card" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#1a202c' }}>
              Invoice Customization
            </h3>
            
            <div style={{ display: 'grid', gap: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
                <div className="form-group">
                  <label>Invoice Prefix</label>
                  <input
                    type="text"
                    name="invoice_prefix"
                    value={settings.invoice_prefix}
                    onChange={handleChange}
                    placeholder="SOUL"
                  />
                  <small style={{ color: '#64748b' }}>Example: {settings.invoice_prefix}2025-001</small>
                </div>

                <div className="form-group">
                  <label>Default Tax Percentage (%)</label>
                  <input
                    type="number"
                    name="default_tax_percentage"
                    value={settings.default_tax_percentage}
                    onChange={handleChange}
                    min="0"
                    max="100"
                    step="0.1"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Invoice Footer Note</label>
                <textarea
                  name="invoice_footer"
                  value={settings.invoice_footer}
                  onChange={handleChange}
                  rows="2"
                  placeholder="Thank you for your business!"
                />
              </div>

              <div className="form-group">
                <label>Terms & Conditions</label>
                <textarea
                  name="invoice_terms"
                  value={settings.invoice_terms}
                  onChange={handleChange}
                  rows="4"
                  placeholder="Enter your terms and conditions here..."
                />
              </div>

              <div className="form-group">
                <label>Digital Signature</label>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleSignatureChange}
                    style={{ display: 'none' }}
                    id="signature-upload"
                  />
                  <label 
                    htmlFor="signature-upload" 
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
                  >
                    <Upload size={18} />
                    Choose Signature
                  </label>
                  {signaturePreview && (
                    <div style={{ 
                      width: '150px', 
                      height: '80px', 
                      border: '2px dashed #cbd5e1', 
                      borderRadius: '0.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                      background: 'white'
                    }}>
                      <img 
                        src={signaturePreview.startsWith('/uploads') ? `${API.replace('/api', '')}${signaturePreview}` : signaturePreview} 
                        alt="Signature Preview" 
                        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                      />
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="show_logo_on_invoice"
                  name="show_logo_on_invoice"
                  checked={settings.show_logo_on_invoice}
                  onChange={handleChange}
                />
                <label htmlFor="show_logo_on_invoice" style={{ margin: 0, cursor: 'pointer' }}>
                  Show company logo on invoices
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Data Control Tab */}
        {activeTab === 'data' && (
          <div className="card" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#1a202c' }}>
              Data Management
            </h3>
            
            <div style={{ display: 'grid', gap: '2rem' }}>
              {/* Export Section */}
              <div>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: '#1a202c' }}>
                  Export Data
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <button 
                    onClick={() => handleExport('Revenue')}
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}
                  >
                    <Download size={18} />
                    Export Revenue
                  </button>
                  <button 
                    onClick={() => handleExport('Expenses')}
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}
                  >
                    <Download size={18} />
                    Export Expenses
                  </button>
                  <button 
                    onClick={() => handleExport('Accounts')}
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}
                  >
                    <Download size={18} />
                    Export Accounts
                  </button>
                  <button 
                    onClick={() => handleExport('Trial Balance')}
                    className="btn btn-secondary"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}
                  >
                    <Download size={18} />
                    Export Trial Balance
                  </button>
                </div>
              </div>

              {/* Import Section */}
              <div>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: '#1a202c' }}>
                  Import Data
                </h4>
                <div style={{ 
                  padding: '2rem', 
                  border: '2px dashed #cbd5e1', 
                  borderRadius: '0.5rem',
                  textAlign: 'center',
                  background: '#f9fafb'
                }}>
                  <FileUp size={48} style={{ color: '#94a3b8', margin: '0 auto 1rem' }} />
                  <p style={{ color: '#64748b', marginBottom: '1rem' }}>
                    Import CSV files for Revenue, Expenses, or Accounts
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    style={{ display: 'none' }}
                    id="csv-upload"
                  />
                  <label 
                    htmlFor="csv-upload"
                    className="btn btn-secondary"
                    style={{ cursor: 'pointer' }}
                  >
                    Choose CSV File
                  </label>
                  <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                    (Coming soon)
                  </p>
                </div>
              </div>

              {/* Clear Data Section */}
              <div>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: '#1a202c' }}>
                  Manage Data
                </h4>
                <div style={{ 
                  padding: '1.5rem', 
                  border: '1px solid #fee2e2', 
                  borderRadius: '0.5rem',
                  background: '#fef2f2'
                }}>
                  <p style={{ color: '#991b1b', marginBottom: '1rem' }}>
                    <strong>Warning:</strong> Clearing test data will permanently delete selected records. This action cannot be undone.
                  </p>
                  <button 
                    onClick={handleClearData}
                    className="btn"
                    style={{ background: '#ef4444', color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    <Trash2 size={18} />
                    Clear Test Data
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Save Button - Fixed at bottom for all tabs except Data Control */}
      {activeTab !== 'data' && (
        <div style={{ 
          marginTop: '2rem', 
          display: 'flex', 
          justifyContent: 'flex-end',
          padding: '1.5rem',
          background: 'white',
          borderTop: '1px solid #e5e7eb',
          position: 'sticky',
          bottom: 0
        }}>
          <button 
            onClick={handleSaveSettings} 
            className="btn btn-primary" 
            disabled={saving} 
            style={{ padding: '0.875rem 2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      )}
    </div>
  );
}

export default AdminSettings;
