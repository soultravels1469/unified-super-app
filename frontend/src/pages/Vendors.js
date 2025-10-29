import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Users } from 'lucide-react';

function Vendors() {
  const [vendors, setVendors] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingVendor, setEditingVendor] = useState(null);
  const [formData, setFormData] = useState({
    vendor_name: '',
    contact: '',
    vendor_type: 'Hotel',
    bank_name: '',
    bank_account_number: '',
    bank_ifsc: ''
  });

  useEffect(() => {
    fetchVendors();
  }, []);

  const fetchVendors = async () => {
    try {
      const response = await axios.get(`${API}/vendors`);
      setVendors(response.data);
    } catch (error) {
      toast.error('Failed to load vendors');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingVendor) {
        await axios.put(`${API}/vendors/${editingVendor.id}`, formData);
        toast.success('Vendor updated');
      } else {
        await axios.post(`${API}/vendors`, formData);
        toast.success('Vendor added');
      }
      setShowForm(false);
      setEditingVendor(null);
      setFormData({ vendor_name: '', contact: '', vendor_type: 'Hotel', bank_name: '', bank_account_number: '', bank_ifsc: '' });
      fetchVendors();
    } catch (error) {
      toast.error('Failed to save vendor');
    }
  };

  const handleEdit = (vendor) => {
    setEditingVendor(vendor);
    setFormData(vendor);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this vendor?')) return;
    try {
      await axios.delete(`${API}/vendors/${id}`);
      toast.success('Vendor deleted');
      fetchVendors();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Users size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Vendors</h1>
        </div>
        <button onClick={() => { setShowForm(true); setEditingVendor(null); setFormData({ vendor_name: '', contact: '', vendor_type: 'Hotel', bank_name: '', bank_account_number: '', bank_ifsc: '' }); }} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={18} />
          Add Vendor
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1rem' }}>
        {vendors.map((vendor) => (
          <div key={vendor.id} className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.25rem' }}>{vendor.vendor_name}</h3>
                <span style={{ fontSize: '0.875rem', background: '#e0e7ff', color: '#4338ca', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>{vendor.vendor_type}</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => handleEdit(vendor)} className="btn btn-secondary" style={{ padding: '0.5rem', minWidth: 'auto' }}>
                  <Edit size={16} />
                </button>
                <button onClick={() => handleDelete(vendor.id)} className="btn" style={{ padding: '0.5rem', minWidth: 'auto', background: '#ef4444', color: 'white' }}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
            <div style={{ fontSize: '0.875rem', color: '#64748b', display: 'grid', gap: '0.25rem' }}>
              {vendor.contact && <div><strong>Contact:</strong> {vendor.contact}</div>}
              {vendor.bank_name && <div><strong>Bank:</strong> {vendor.bank_name}</div>}
              {vendor.bank_account_number && <div><strong>Account:</strong> {vendor.bank_account_number}</div>}
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card" style={{ width: '90%', maxWidth: '600px', padding: '2rem', maxHeight: '90vh', overflow: 'auto' }}>
            <h2 style={{ marginBottom: '1.5rem' }}>{editingVendor ? 'Edit' : 'Add'} Vendor</h2>
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div className="form-group">
                  <label>Vendor Name *</label>
                  <input type="text" value={formData.vendor_name} onChange={(e) => setFormData({...formData, vendor_name: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Contact</label>
                  <input type="text" value={formData.contact} onChange={(e) => setFormData({...formData, contact: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Vendor Type *</label>
                  <select value={formData.vendor_type} onChange={(e) => setFormData({...formData, vendor_type: e.target.value})} required>
                    <option value="Hotel">Hotel</option>
                    <option value="Flight">Flight</option>
                    <option value="Package">Package</option>
                    <option value="Insurance">Insurance</option>
                    <option value="Visa">Visa</option>
                    <option value="Land">Land/Transport</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Bank Name (Optional)</label>
                  <input type="text" value={formData.bank_name} onChange={(e) => setFormData({...formData, bank_name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Bank Account Number (Optional)</label>
                  <input type="text" value={formData.bank_account_number} onChange={(e) => setFormData({...formData, bank_account_number: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Bank IFSC (Optional)</label>
                  <input type="text" value={formData.bank_ifsc} onChange={(e) => setFormData({...formData, bank_ifsc: e.target.value})} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => { setShowForm(false); setEditingVendor(null); }} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Vendors;