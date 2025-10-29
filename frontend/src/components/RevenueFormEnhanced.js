import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { X, Plus, Trash2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

function RevenueFormEnhanced({ revenue, onClose, defaultSource = '' }) {
  // Get today's date in YYYY-MM-DD format
  const getTodayDate = () => new Date().toISOString().split('T')[0];
  
  const [formData, setFormData] = useState({
    date: getTodayDate(),
    client_name: '',
    source: defaultSource || 'Visa',
    payment_mode: 'Cash',
    sale_price: 0,
    received_amount: 0,
    pending_amount: 0,
    status: 'Pending',
    notes: '',
    cost_price_details: [],
    partial_payments: []
  });

  const [vendors, setVendors] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [costRows, setCostRows] = useState([]);
  const [partialPayments, setPartialPayments] = useState([]);
  const [showPartialPayments, setShowPartialPayments] = useState(false);
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    fetchVendors();
    fetchBankAccounts();
    
    if (revenue) {
      setFormData(revenue);
      setCostRows(revenue.cost_price_details || []);
      setPartialPayments(revenue.partial_payments || []);
      setShowPartialPayments((revenue.partial_payments || []).length > 0);
    }
  }, [revenue]);

  const fetchVendors = async () => {
    try {
      const response = await axios.get(`${API}/vendors`);
      setVendors(response.data);
    } catch (error) {
      console.error('Failed to load vendors');
    }
  };

  const fetchBankAccounts = async () => {
    try {
      const response = await axios.get(`${API}/bank-accounts`);
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Failed to load bank accounts');
    }
  };

  // Real-time calculation with validation
  const validateAndCalculate = (salePrice, receivedAmount, pendingAmount, changedField) => {
    const s = parseFloat(salePrice) || 0;
    const x = parseFloat(receivedAmount) || 0;
    const y = parseFloat(pendingAmount) || 0;

    let newReceived = x;
    let newPending = y;
    let error = '';

    // Auto-calculate based on which field changed
    if (changedField === 'sale_price') {
      newPending = s - x;
    } else if (changedField === 'received_amount') {
      newPending = s - x;
    } else if (changedField === 'pending_amount') {
      newReceived = s - y;
    }

    // Validation: x + y should equal s
    if (Math.abs((newReceived + newPending) - s) > 0.01 && s > 0) {
      error = `⚠️ Mismatch: Received (₹${newReceived}) + Pending (₹${newPending}) ≠ Sale Price (₹${s})`;
    }

    setValidationError(error);

    return {
      received_amount: newReceived,
      pending_amount: newPending,
      status: newPending > 0 ? 'Pending' : 'Completed'
    };
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    let updatedData = { ...formData, [name]: value };

    // Auto-calculation for financial fields
    if (['sale_price', 'received_amount', 'pending_amount'].includes(name)) {
      const calculated = validateAndCalculate(
        name === 'sale_price' ? value : formData.sale_price,
        name === 'received_amount' ? value : formData.received_amount,
        name === 'pending_amount' ? value : formData.pending_amount,
        name
      );
      updatedData = { ...updatedData, ...calculated };
    }

    setFormData(updatedData);
  };

  // Cost Row Management
  const addCostRow = () => {
    setCostRows([...costRows, {
      id: `temp_${Date.now()}`,
      vendor_name: '',
      category: 'Hotel',
      amount: 0,
      payment_date: formData.date || getTodayDate(),
      payment_status: 'Done',
      pending_amount: 0,
      due_date: '',
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
    
    // If payment status changes to "Pending", ensure pending_amount and due_date are filled
    if (field === 'payment_status' && value === 'Pending') {
      if (!newRows[index].pending_amount) {
        newRows[index].pending_amount = newRows[index].amount;
      }
    }
    
    setCostRows(newRows);
  };

  // Partial Payment Management
  const addPartialPayment = () => {
    setPartialPayments([...partialPayments, {
      id: `payment_${Date.now()}`,
      date: getTodayDate(),
      amount: 0,
      bank_name: bankAccounts[0]?.bank_name || '',
      payment_mode: 'Bank Transfer',
      notes: ''
    }]);
    setShowPartialPayments(true);
  };

  const removePartialPayment = (index) => {
    const newPayments = partialPayments.filter((_, i) => i !== index);
    setPartialPayments(newPayments);
  };

  const updatePartialPayment = (index, field, value) => {
    const newPayments = [...partialPayments];
    newPayments[index][field] = value;
    setPartialPayments(newPayments);

    // Auto-update received amount based on partial payments
    const totalPartialPayments = newPayments.reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
    const calculated = validateAndCalculate(
      formData.sale_price,
      totalPartialPayments,
      formData.pending_amount,
      'received_amount'
    );
    setFormData({ ...formData, ...calculated, received_amount: totalPartialPayments });
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

    if (validationError) {
      toast.error('Please fix validation errors before submitting');
      return;
    }

    const { totalCost, profit, profitMargin } = calculateTotals();
    
    const submitData = {
      ...formData,
      cost_price_details: costRows,
      partial_payments: partialPayments,
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
      overflow: 'auto',
      padding: '1rem'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '2rem',
        width: '95%',
        maxWidth: '1200px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>
            {revenue ? 'Edit Revenue' : 'Add Revenue'} - Complete Tracking
          </h2>
          <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: '0.5rem' }}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Basic Info Section */}
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: '#1a202c' }}>Basic Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
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
                  <option value="Insurance">Insurance</option>
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
          </div>

          {/* Payment Details Section */}
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: '#1a202c' }}>Payment Details</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div className="form-group">
                <label>Received Amount (₹)</label>
                <input 
                  type="number" 
                  name="received_amount" 
                  value={formData.received_amount} 
                  onChange={handleChange}
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="form-group">
                <label>Payment Mode</label>
                <select name="payment_mode" value={formData.payment_mode} onChange={handleChange}>
                  <option value="Cash">Cash</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                  <option value="UPI">UPI</option>
                  <option value="Cheque">Cheque</option>
                </select>
              </div>

              <div className="form-group">
                <label>Pending Amount (₹)</label>
                <input 
                  type="number" 
                  name="pending_amount" 
                  value={formData.pending_amount} 
                  onChange={handleChange}
                  min="0"
                  step="0.01"
                  readOnly
                  style={{ background: '#f3f4f6' }}
                />
              </div>

              <div className="form-group">
                <label>Status</label>
                <div style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  fontWeight: 600,
                  textAlign: 'center',
                  background: formData.status === 'Completed' ? '#d1fae5' : '#fed7aa',
                  color: formData.status === 'Completed' ? '#065f46' : '#9a3412'
                }}>
                  {formData.status}
                </div>
              </div>
            </div>

            {/* Validation Error */}
            {validationError && (
              <div style={{ 
                marginTop: '1rem',
                padding: '0.75rem',
                background: '#fef2f2',
                border: '1px solid '#fecaca',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: '#991b1b'
              }}>
                <AlertCircle size={18} />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          {/* Partial Payments Section */}
          {formData.pending_amount > 0 && (
            <div style={{ marginBottom: '2rem' }}>
              <div 
                onClick={() => setShowPartialPayments(!showPartialPayments)}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  cursor: 'pointer',
                  padding: '1rem',
                  background: '#f0f9ff',
                  borderRadius: '8px',
                  marginBottom: '1rem'
                }}
              >
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>
                  Partial Payments ({partialPayments.length})
                </h3>
                {showPartialPayments ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </div>

              {showPartialPayments && (
                <div style={{ padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
                  <button 
                    type="button"
                    onClick={addPartialPayment}
                    className="btn btn-secondary"
                    style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    <Plus size={16} />
                    Add Partial Payment
                  </button>

                  {partialPayments.map((payment, index) => (
                    <div key={payment.id} style={{ 
                      marginBottom: '1rem',
                      padding: '1rem',
                      background: '#f9fafb',
                      borderRadius: '8px',
                      border: '1px solid #e5e7eb'
                    }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1.5fr auto', gap: '0.75rem', alignItems: 'end' }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem' }}>Date</label>
                          <input
                            type="date"
                            value={payment.date}
                            onChange={(e) => updatePartialPayment(index, 'date', e.target.value)}
                            required
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem' }}>Amount (₹)</label>
                          <input
                            type="number"
                            value={payment.amount}
                            onChange={(e) => updatePartialPayment(index, 'amount', parseFloat(e.target.value) || 0)}
                            min="0"
                            step="0.01"
                            required
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem' }}>Bank</label>
                          <select
                            value={payment.bank_name}
                            onChange={(e) => updatePartialPayment(index, 'bank_name', e.target.value)}
                          >
                            <option value="">Select Bank</option>
                            {bankAccounts.map(bank => (
                              <option key={bank.id} value={bank.bank_name}>{bank.bank_name}</option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem' }}>Payment Mode</label>
                          <select
                            value={payment.payment_mode}
                            onChange={(e) => updatePartialPayment(index, 'payment_mode', e.target.value)}
                          >
                            <option value="Cash">Cash</option>
                            <option value="Bank Transfer">Bank Transfer</option>
                            <option value="UPI">UPI</option>
                            <option value="Cheque">Cheque</option>
                          </select>
                        </div>

                        <button
                          type="button"
                          onClick={() => removePartialPayment(index)}
                          style={{ 
                            border: 'none',
                            background: '#ef4444',
                            color: 'white',
                            padding: '0.5rem',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}

                  <div style={{ 
                    marginTop: '1rem',
                    padding: '0.75rem',
                    background: '#f0f9ff',
                    borderRadius: '6px',
                    fontWeight: 600
                  }}>
                    Total Partial Payments: ₹{partialPayments.reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Profit Summary */}
          <div style={{ 
            background: '#f0f9ff', 
            padding: '1rem', 
            borderRadius: '8px', 
            marginBottom: '2rem',
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
          <div style={{ marginBottom: '2rem' }}>
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
              💡 Each cost entry auto-creates Expense records and syncs with vendor ledger
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
                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1.5fr auto', gap: '0.75rem', alignItems: 'end', marginBottom: '0.75rem' }}>
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.875rem' }}>Vendor *</label>
                        <select
                          value={row.vendor_name}
                          onChange={(e) => updateCostRow(index, 'vendor_name', e.target.value)}
                          required
                        >
                          <option value="">Select Vendor</option>
                          {vendors.map(vendor => (
                            <option key={vendor.id} value={vendor.vendor_name}>{vendor.vendor_name}</option>
                          ))}
                        </select>
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
                        <label style={{ fontSize: '0.875rem' }}>Amount (₹) *</label>
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

                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontSize: '0.875rem' }}>Payment Status</label>
                        <select
                          value={row.payment_status}
                          onChange={(e) => updateCostRow(index, 'payment_status', e.target.value)}
                        >
                          <option value="Done">Done</option>
                          <option value="Pending">Pending</option>
                        </select>
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
                          cursor: 'pointer'
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>

                    {/* Pending Payment Details */}
                    {row.payment_status === 'Pending' && (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: '0.75rem', marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #e5e7eb' }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem', color: '#ef4444' }}>Pending Amount (₹)</label>
                          <input
                            type="number"
                            value={row.pending_amount || 0}
                            onChange={(e) => updateCostRow(index, 'pending_amount', parseFloat(e.target.value) || 0)}
                            min="0"
                            step="0.01"
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem', color: '#ef4444' }}>Due Date</label>
                          <input
                            type="date"
                            value={row.due_date || ''}
                            onChange={(e) => updateCostRow(index, 'due_date', e.target.value)}
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '0.875rem' }}>Notes</label>
                          <input
                            type="text"
                            value={row.notes || ''}
                            onChange={(e) => updateCostRow(index, 'notes', e.target.value)}
                            placeholder="Payment pending notes..."
                          />
                        </div>
                      </div>
                    )}
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
                <p style={{ color: '#64748b', margin: 0 }}>No vendor costs added yet</p>
              </div>
            )}
          </div>

          {/* Additional Notes */}
          <div className="form-group" style={{ marginBottom: '2rem' }}>
            <label>Additional Notes</label>
            <textarea 
              name="notes" 
              value={formData.notes} 
              onChange={handleChange}
              rows="3"
              placeholder="Any additional information..."
            />
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', paddingTop: '1rem', borderTop: '2px solid #e5e7eb' }}>
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
              disabled={!!validationError}
            >
              {revenue ? 'Update Revenue' : 'Create Revenue & Sync Ledgers'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RevenueFormEnhancedFinal;
