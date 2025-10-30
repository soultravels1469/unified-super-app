import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Users, AlertCircle, CheckCircle, Clock } from 'lucide-react';

function VendorPayments() {
  const [vendorPayments, setVendorPayments] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVendorPayments();
  }, []);

  const fetchVendorPayments = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const revenues = response.data;
      
      const vendors = [];
      revenues.forEach(rev => {
        (rev.cost_price_details || []).forEach(vendor => {
          const totalPaid = (vendor.vendor_payments || []).reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
          const pendingAmount = (parseFloat(vendor.amount) || 0) - totalPaid;
          
          vendors.push({
            id: `${rev.id}_${vendor.vendor_name}`,
            vendor_name: vendor.vendor_name,
            vendor_type: vendor.vendor_type || 'Hotel',
            vendor_note: vendor.vendor_note || '',
            due_date: rev.date,
            pending_amount: pendingAmount,
            status: vendor.payment_status || (pendingAmount > 0 ? 'Pending' : 'Done'),
            client_name: rev.client_name
          });
        });
      });

      setVendorPayments(vendors);
    } catch (error) {
      console.error('Failed to load vendor payments');
    } finally {
      setLoading(false);
    }
  };

  const getFilteredVendors = () => {
    const today = new Date();
    const sevenDaysLater = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

    return vendorPayments.filter(vendor => {
      const dueDate = new Date(vendor.due_date);
      
      if (filter === 'upcoming') {
        return vendor.pending_amount > 0 && dueDate >= today && dueDate <= sevenDaysLater;
      } else if (filter === 'overdue') {
        return vendor.pending_amount > 0 && dueDate < today;
      } else if (filter === 'pending') {
        return vendor.pending_amount > 0;
      }
      return true;
    }).sort((a, b) => new Date(a.due_date) - new Date(b.due_date));
  };

  const getStatusColor = (vendor) => {
    if (vendor.pending_amount <= 0) return { bg: '#d1fae5', text: '#065f46', icon: CheckCircle };
    
    const dueDate = new Date(vendor.due_date);
    const today = new Date();
    const sevenDaysLater = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
    
    if (dueDate < today) return { bg: '#fee2e2', text: '#991b1b', icon: AlertCircle };
    if (dueDate <= sevenDaysLater) return { bg: '#fef3c7', text: '#92400e', icon: Clock };
    return { bg: '#e0e7ff', text: '#3730a3', icon: Clock };
  };

  const filteredVendors = getFilteredVendors();

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container">
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <Users size={32} style={{ color: '#3b82f6' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Vendor Payments</h1>
        </div>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[
            { key: 'all', label: 'All Vendors' },
            { key: 'pending', label: 'Pending' },
            { key: 'upcoming', label: 'Upcoming (7 days)' },
            { key: 'overdue', label: 'Overdue' }
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: filter === f.key ? '#3b82f6' : '#f3f4f6',
                color: filter === f.key ? 'white' : '#374151',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontWeight: '500',
                fontSize: '0.875rem'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {filteredVendors.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No vendor payments found for this filter.
        </div>
      ) : (
        <div style={{ backgroundColor: 'white', borderRadius: '0.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
              <tr>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>#</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Vendor Name</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Phone</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Client</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Due Date</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Pending (₹)</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'center', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredVendors.map((vendor, index) => {
                const statusColor = getStatusColor(vendor);
                const StatusIcon = statusColor.icon;
                
                return (
                  <tr key={vendor.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '1rem', color: '#6b7280', fontWeight: '500' }}>{index + 1}</td>
                    <td style={{ padding: '1rem', fontWeight: '600', color: '#111827' }}>{vendor.vendor_name}</td>
                    <td style={{ padding: '1rem', color: '#6b7280' }}>{vendor.vendor_phone || '-'}</td>
                    <td style={{ padding: '1rem', color: '#6b7280' }}>{vendor.client_name}</td>
                    <td style={{ padding: '1rem', color: '#6b7280' }}>{new Date(vendor.due_date).toLocaleDateString()}</td>
                    <td style={{ padding: '1rem', textAlign: 'right', fontWeight: '600', color: vendor.pending_amount > 0 ? '#dc2626' : '#16a34a' }}>
                      ₹{vendor.pending_amount.toFixed(2)}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.25rem 0.75rem',
                        backgroundColor: statusColor.bg,
                        color: statusColor.text,
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        <StatusIcon size={14} />
                        {vendor.pending_amount > 0 ? 'Pending' : 'Cleared'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default VendorPayments;
