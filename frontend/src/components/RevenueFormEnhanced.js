import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { X, Plus, Trash2 } from 'lucide-react';

function RevenueFormEnhanced({ revenue, onClose, defaultSource = '' }) {
  const [formData, setFormData] = useState({
    date: '',
    client_name: '',
    source: defaultSource || 'Visa',
    payment_mode: 'Cash',
    pending_amount: 0,
    received_amount: 0,
    status: 'Pending',
    supplier: '',
    notes: '',
    sale_price: 0,
    cost_price_details: []
  });

  const [costRows, setCostRows] = useState([]);

  useEffect(() => {
    if (revenue) {
      setFormData(revenue);
      setCostRows(revenue.cost_price_details || []);
    }
  }, [revenue]);

  const addCostRow = () => {
    setCostRows([...costRows, {
      id: `temp_${Date.now()}`,
      vendor_name: '',
      category: 'Hotel',
      amount: 0,
      payment_date: formData.date || new Date().toISOString().split('T')[0],
      notes: ''
    }]);
  };

  const removeCostRow = (index) => {
    const newRows = costRows.filter((_, i) => i !== index);
    setCostRows(newRows);
  };

  const updateCostRow = (index, field, value) => {
    const newRows = [...costRows];
    newRows[index][field] = value;
    setCostRows(newRows);
  };

  const calculateTotals = () => {
    const totalCost = costRows.reduce((sum, row) => sum + (parseFloat(row.amount) || 0), 0);
    const salePrice = parseFloat(formData.sale_price) || 0;
    const profit = salePrice - totalCost;
    const profitMargin = salePrice > 0 ? ((profit / salePrice) * 100).toFixed(2) : 0;
    
    return { totalCost, profit, profitMargin };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const { totalCost, profit, profitMargin } = calculateTotals();
    
    const submitData = {
      ...formData,
      cost_price_details: costRows,
      total_cost_price: totalCost,
      profit: profit,
      profit_margin: profitMargin
    };

    try {
      if (revenue) {
        await axios.put(`${API}/revenue/${revenue.id}`, submitData);
        toast.success('Revenue updated successfully');
      } else {
        await axios.post(`${API}/revenue`, submitData);
        toast.success('Revenue added successfully');
      }
      onClose();
    } catch (error) {
      toast.error('Failed to save revenue');
      console.error(error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    let updatedData = {
      ...formData,
      [name]: value,
    };

    // Auto-calculate amounts based on status
    if (name === 'status') {
      if (value === 'Received') {
        updatedData.received_amount = formData.sale_price || 0;
        updatedData.pending_amount = 0;
      } else if (value === 'Pending') {
        updatedData.received_amount = 0;
        updatedData.pending_amount = formData.sale_price || 0;
      }
    }

    setFormData(updatedData);
  };

  const { totalCost, profit, profitMargin } = calculateTotals();

  return (
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
      zIndex: 1000,
      overflow: 'auto'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '2rem',
        width: '95%',
        maxWidth: '900px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>
            {revenue ? 'Edit Revenue' : 'Add Revenue'} - With Cost Tracking
          </h2>
          <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: '0.5rem' }}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Basic Info */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>Date *</label>
              <input type="date" name="date" value={formData.date} onChange={handleChange} required />
            </div>

            <div className="form-group">
              <label>Client Name *</label>
              <input type="text" name="client_name" value={formData.client_name} onChange={handleChange} required />
            </div>

            <div className="form-group">
              <label>Source *</label>
              <select name="source" value={formData.source} onChange={handleChange} required>
                <option value="Visa">Visa</option>
                <option value="Ticket">Ticket</option>
                <option value="Package">Package</option>
              </select>
            </div>

            <div className="form-group">
              <label>Payment Mode *</label>
              <select name="payment_mode" value={formData.payment_mode} onChange={handleChange}>
                <option value="Cash">Cash</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="UPI">UPI</option>
              </select>
            </div>

            <div className="form-group">
              <label>Status *</label>
              <select name="status" value={formData.status} onChange={handleChange}>
                <option value="Pending">Pending</option>
                <option value="Received">Received</option>
              </select>
            </div>

            <div className="form-group">
              <label>Sale Price (₹) *</label>
              <input 
                type="number" 
                name="sale_price" 
                value={formData.sale_price} 
                onChange={handleChange}
                min="0"
                step="0.01"
                required 
              />
            </div>
          </div>

          {/* Profit Summary Card */}
          <div style={{ 
            background: '#f0f9ff', 
            padding: '1rem', 
            borderRadius: '8px', 
            marginBottom: '1.5rem',
            border: '1px solid #bae6fd'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Sale Price</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#10b981' }}>
                  ₹{parseFloat(formData.sale_price || 0).toLocaleString()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Total Cost</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#ef4444' }}>
                  ₹{totalCost.toLocaleString()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Profit</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, color: profit >= 0 ? '#10b981' : '#ef4444' }}>
                  ₹{profit.toLocaleString()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>Profit %</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, color: profit >= 0 ? '#10b981' : '#ef4444' }}>
                  {profitMargin}%
                </div>
              </div>
            </div>
          </div>

          {/* Vendor Cost Breakdown */}
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Vendor Cost Breakdown</h3>
              <button 
                type="button"
                onClick={addCostRow}
                className="btn btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem' }}
              >
                <Plus size={16} />
                Add Vendor Cost
              </button>
            </div>

            <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '1rem' }}>
              💡 Note: Each cost entry will auto-create an Expense record for accounting.
            </p>

            {costRows.length > 0 ? (
              <div style={{ display: 'grid', gap: '1rem' }}>
                {costRows.map((row, index) => (
                  <div key={row.id || index} style={{ 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px', 
                    padding: '1rem',
                    background: '#f9fafb'
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr 1fr 1.5fr auto', gap: '0.75rem', alignItems: 'end' }}>
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.875rem' }}>Vendor Name</label>
                        <input
                          type="text"
                          value={row.vendor_name}
                          onChange={(e) => updateCostRow(index, 'vendor_name', e.target.value)}
                          required
                        />
                      </div>

                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.875rem' }}>Category</label>
                        <select
                          value={row.category}
                          onChange={(e) => updateCostRow(index, 'category', e.target.value)}
                        >
                          <option value="Hotel">Hotel</option>
                          <option value="Flight">Flight</option>
                          <option value="Land">Land</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>

                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.875rem' }}>Amount (₹)</label>
                        <input
                          type="number"
                          value={row.amount}
                          onChange={(e) => updateCostRow(index, 'amount', parseFloat(e.target.value) || 0)}
                          min="0"
                          step="0.01"
                          required
                        />
                      </div>

                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.875rem' }}>Payment Date</label>
                        <input
                          type="date"
                          value={row.payment_date}
                          onChange={(e) => updateCostRow(index, 'payment_date', e.target.value)}
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() => removeCostRow(index)}
                        style={{ 
                          border: 'none',
                          background: '#ef4444',
                          color: 'white',
                          padding: '0.5rem',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>

                    <div className="form-group" style={{ marginTop: '0.5rem', marginBottom: 0 }}>
                      <label style={{ fontSize: '0.875rem' }}>Notes (Optional)</label>
                      <input
                        type="text"
                        value={row.notes}
                        onChange={(e) => updateCostRow(index, 'notes', e.target.value)}
                        placeholder="Any additional notes..."
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '2rem', 
                background: '#f9fafb', 
                borderRadius: '8px',
                border: '2px dashed #e5e7eb'
              }}>
                <p style={{ color: '#64748b', margin: 0 }}>No vendor costs added yet. Click "Add Vendor Cost" to get started.</p>
              </div>
            )}
          </div>

          {/* Additional Info */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>Received Amount (₹)</label>
              <input 
                type="number" 
                name="received_amount" 
                value={formData.received_amount} 
                onChange={handleChange}
                min="0"
              />
            </div>

            <div className="form-group">
              <label>Pending Amount (₹)</label>
              <input 
                type="number" 
                name="pending_amount" 
                value={formData.pending_amount} 
                onChange={handleChange}
                min="0"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label>Notes (Optional)</label>
            <textarea 
              name="notes" 
              value={formData.notes} 
              onChange={handleChange}
              rows="3"
            />
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button 
              type="button" 
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button 
              type="submit"
              className="btn btn-primary"
            >
              {revenue ? 'Update Revenue' : 'Create Revenue'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RevenueFormEnhanced;
