import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { X, Plus, Trash2, ChevronDown, ChevronUp, AlertCircle, DollarSign, Users, Calendar, CreditCard } from 'lucide-react';

const PAYMENT_MODES = ["Cash", "Bank Transfer", "UPI", "Cheque", "Debit Card", "Credit Card", "Pending"];
const VENDOR_TYPES = ["Hotel", "Land", "Visa", "Insurance", "Others"];

function RevenueFormEnhanced({ revenue, onClose, defaultSource = '' }) {
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
    partial_payments: [],
    travel_start_date: null,
    lead_id: null
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
      const payments = revenue.partial_payments || [];
      setPartialPayments(payments);
      setShowPartialPayments(payments.length > 0);
      
      // Fetch travel date from CRM if lead_id exists
      if (revenue.lead_id) {
        fetchTravelDate(revenue.lead_id);
      }
    }
  }, [revenue]);

  // Force expand if > 1 partial payment
  useEffect(() => {
    if (partialPayments.length > 1) {
      setShowPartialPayments(true);
    }
  }, [partialPayments.length]);

  const fetchTravelDate = async (leadId) => {
    try {
      const response = await axios.get(`${API}/crm/leads?search=${leadId}`);
      if (response.data && response.data.leads && response.data.leads.length > 0) {
        const lead = response.data.leads[0];
        if (lead.travel_date) {
          setFormData(prev => ({ ...prev, travel_start_date: lead.travel_date }));
        }
      }
    } catch (error) {
      console.error('Failed to fetch travel date');
    }
  };

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

  const validateAndCalculate = (salePrice, receivedAmount, pendingAmount, changedField) => {
    const s = parseFloat(salePrice) || 0;
    const x = parseFloat(receivedAmount) || 0;
    const y = parseFloat(pendingAmount) || 0;

    let newReceived = x;
    let newPending = y;
    let error = '';

    if (changedField === 'sale_price') {
      newPending = s - x;
    } else if (changedField === 'received_amount') {
      newPending = s - x;
    } else if (changedField === 'pending_amount') {
      newReceived = s - y;
    }

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

  const handleChange = (field, value, changedField = null) => {
    let updates = { [field]: value };

    if (['sale_price', 'received_amount', 'pending_amount'].includes(field)) {
      const calculated = validateAndCalculate(
        field === 'sale_price' ? value : formData.sale_price,
        field === 'received_amount' ? value : formData.received_amount,
        field === 'pending_amount' ? value : formData.pending_amount,
        changedField || field
      );
      updates = { ...updates, ...calculated };
    }

    setFormData({ ...formData, ...updates });
  };

  const addCostRow = () => {
    setCostRows([...costRows, {
      id: `cost_${Date.now()}`,
      vendor_name: vendors[0]?.vendor_name || '',
      vendor_type: 'Hotel',
      vendor_note: '',
      amount: 0,
      payment_status: 'Pending',
      vendor_payments: []
    }]);
  };

  const removeCostRow = (index) => {
    setCostRows(costRows.filter((_, i) => i !== index));
  };

  const updateCostRow = (index, field, value) => {
    const newRows = [...costRows];
    newRows[index][field] = value;

    // Auto-calculate pending and update status
    if (field === 'vendor_payments') {
      const totalPaid = value.reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
      const totalPayable = parseFloat(newRows[index].amount) || 0;
      const pending = totalPayable - totalPaid;
      
      // Auto-update status when pending = 0
      if (pending <= 0.01 && totalPayable > 0) {
        newRows[index].payment_status = 'Done';
      } else {
        newRows[index].payment_status = 'Pending';
      }
    }

    setCostRows(newRows);
  };

  const addVendorPayment = (costIndex) => {
    const newRows = [...costRows];
    const vendorPayments = newRows[costIndex].vendor_payments || [];
    vendorPayments.push({
      id: `vpayment_${Date.now()}`,
      date: getTodayDate(),
      amount: 0,
      mode: 'Pending',  // Default mode
      transaction_number: '',
      bank_name: bankAccounts[0]?.bank_name || ''
    });
    newRows[costIndex].vendor_payments = vendorPayments;
    updateCostRow(costIndex, 'vendor_payments', vendorPayments);
  };

  const removeVendorPayment = (costIndex, paymentIndex) => {
    const newRows = [...costRows];
    newRows[costIndex].vendor_payments = newRows[costIndex].vendor_payments.filter((_, i) => i !== paymentIndex);
    updateCostRow(costIndex, 'vendor_payments', newRows[costIndex].vendor_payments);
  };

  const updateVendorPayment = (costIndex, paymentIndex, field, value) => {
    const newRows = [...costRows];
    newRows[costIndex].vendor_payments[paymentIndex][field] = value;
    updateCostRow(costIndex, 'vendor_payments', newRows[costIndex].vendor_payments);
  };

  const addPartialPayment = () => {
    setPartialPayments([...partialPayments, {
      id: `payment_${Date.now()}`,
      date: getTodayDate(),
      amount: 0,
      bank_name: bankAccounts[0]?.bank_name || '',
      payment_mode: 'Bank Transfer',
      transaction_number: '',
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
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '900px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        {/* Header */}
        <div style={{ padding: '1.5rem', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>
            {revenue ? 'Edit Revenue' : 'Add Revenue'}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          {/* Revenue Details Section - Light Blue */}
          <div style={{ backgroundColor: '#eff6ff', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid #dbeafe' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <DollarSign size={20} style={{ color: '#3b82f6' }} />
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0, color: '#1e40af' }}>Revenue Details</h3>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Date *
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                  required
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Client Name *
                </label>
                <input
                  type="text"
                  value={formData.client_name}
                  onChange={(e) => handleChange('client_name', e.target.value)}
                  required
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Service Type *
                </label>
                <select
                  value={formData.source}
                  onChange={(e) => handleChange('source', e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                >
                  <option value="Visa">Visa</option>
                  <option value="Ticket">Ticket</option>
                  <option value="Package">Package</option>
                  <option value="Insurance">Insurance</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Sale Price (₹) *
                </label>
                <input
                  type="number"
                  value={formData.sale_price}
                  onChange={(e) => handleChange('sale_price', parseFloat(e.target.value) || 0, 'sale_price')}
                  required
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Received Amount (₹)
                </label>
                <input
                  type="number"
                  value={formData.received_amount}
                  onChange={(e) => handleChange('received_amount', parseFloat(e.target.value) || 0, 'received_amount')}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Pending Amount (₹)
                </label>
                <input
                  type="number"
                  value={formData.pending_amount}
                  onChange={(e) => handleChange('pending_amount', parseFloat(e.target.value) || 0, 'pending_amount')}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                />
              </div>
            </div>

            {validationError && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.375rem' }}>
                <AlertCircle size={18} style={{ color: '#dc2626' }} />
                <span style={{ fontSize: '0.875rem', color: '#dc2626' }}>{validationError}</span>
              </div>
            )}
          </div>

          {/* Travel Info Section - Light Gray */}
          {formData.travel_start_date && (
            <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid #e5e7eb' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Calendar size={20} style={{ color: '#6b7280' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0, color: '#374151' }}>Travel Information (from CRM)</h3>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem', color: '#374151' }}>
                  Travel Start Date
                </label>
                <input
                  type="date"
                  value={formData.travel_start_date ? new Date(formData.travel_start_date).toISOString().split('T')[0] : ''}
                  readOnly
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', backgroundColor: '#f3f4f6' }}
                />
              </div>
            </div>
          )}

          {/* Vendor Breakdown Section - Light Green */}
          <div style={{ backgroundColor: '#f0fdf4', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid #dcfce7' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={20} style={{ color: '#16a34a' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0, color: '#15803d' }}>Vendor Breakdown</h3>
              </div>
              <button
                type="button"
                onClick={addCostRow}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', backgroundColor: '#16a34a', color: 'white', border: 'none', borderRadius: '0.375rem', cursor: 'pointer' }}
              >
                <Plus size={18} />
                Add Vendor
              </button>
            </div>

            {costRows.map((row, index) => {
              const totalPaid = (row.vendor_payments || []).reduce((sum, p) => sum + (parseFloat(p.amount) || 0), 0);
              const pendingAmount = (parseFloat(row.amount) || 0) - totalPaid;

              return (
                <div key={row.id} style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1rem', border: '1px solid #d1fae5' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <span style={{ fontWeight: '600', color: '#16a34a', fontSize: '1rem' }}>Vendor #{index + 1}</span>
                    <button
                      type="button"
                      onClick={() => removeCostRow(index)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>Vendor Name</label>
                      <select
                        value={row.vendor_name}
                        onChange={(e) => updateCostRow(index, 'vendor_name', e.target.value)}
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      >
                        <option value="">Select Vendor</option>
                        {vendors.map((v) => (
                          <option key={v._id} value={v.vendor_name}>{v.vendor_name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>Phone</label>
                      <input
                        type="text"
                        value={row.vendor_phone || ''}
                        onChange={(e) => updateCostRow(index, 'vendor_phone', e.target.value)}
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>Amount Payable (₹)</label>
                      <input
                        type="number"
                        value={row.amount}
                        onChange={(e) => updateCostRow(index, 'amount', parseFloat(e.target.value) || 0)}
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>Pending Amount (₹)</label>
                      <input
                        type="number"
                        value={pendingAmount.toFixed(2)}
                        readOnly
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', backgroundColor: '#f3f4f6', fontWeight: '600', color: pendingAmount > 0 ? '#dc2626' : '#16a34a' }}
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => addVendorPayment(index)}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', backgroundColor: '#16a34a', color: 'white', border: 'none', borderRadius: '0.375rem', cursor: 'pointer', fontSize: '0.875rem' }}
                  >
                    <Plus size={16} />
                    Add Payment
                  </button>

                  {(row.vendor_payments || []).map((payment, pIdx) => (
                    <div key={payment.id} style={{ backgroundColor: '#f9fafb', padding: '1rem', borderRadius: '0.375rem', marginTop: '0.75rem', border: '1px solid #e5e7eb' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Date</label>
                          <input
                            type="date"
                            value={payment.date}
                            onChange={(e) => updateVendorPayment(index, pIdx, 'date', e.target.value)}
                            style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Amount</label>
                          <input
                            type="number"
                            value={payment.amount}
                            onChange={(e) => updateVendorPayment(index, pIdx, 'amount', parseFloat(e.target.value) || 0)}
                            style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Mode</label>
                          <select
                            value={payment.mode}
                            onChange={(e) => updateVendorPayment(index, pIdx, 'mode', e.target.value)}
                            style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                          >
                            {PAYMENT_MODES.map(mode => <option key={mode} value={mode}>{mode}</option>)}
                          </select>
                        </div>

                        <div style={{ gridColumn: 'span 2' }}>
                          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Check/Transaction Number</label>
                          <input
                            type="text"
                            value={payment.transaction_number || ''}
                            onChange={(e) => updateVendorPayment(index, pIdx, 'transaction_number', e.target.value)}
                            placeholder="Optional"
                            style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                          />
                        </div>

                        <button
                          type="button"
                          onClick={() => removeVendorPayment(index, pIdx)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', padding: '0.375rem' }}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>

          {/* Partial Payments Section - Light Yellow */}
          <div style={{ backgroundColor: '#fefce8', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid #fef08a' }}>
            <div
              onClick={() => setShowPartialPayments(!showPartialPayments)}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', marginBottom: showPartialPayments ? '1rem' : 0 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CreditCard size={20} style={{ color: '#ca8a04' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0, color: '#a16207' }}>Partial Payments ({partialPayments.length})</h3>
              </div>
              {partialPayments.length <= 1 ? (
                showPartialPayments ? <ChevronUp size={20} /> : <ChevronDown size={20} />
              ) : null}
            </div>

            {showPartialPayments && (
              <>
                <button
                  type="button"
                  onClick={addPartialPayment}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', backgroundColor: '#ca8a04', color: 'white', border: 'none', borderRadius: '0.375rem', cursor: 'pointer', marginBottom: '1rem' }}
                >
                  <Plus size={18} />
                  Add Partial Payment
                </button>

                {partialPayments.map((payment, index) => (
                  <div key={payment.id} style={{ backgroundColor: 'white', padding: '1rem', borderRadius: '0.375rem', marginBottom: '0.75rem', border: '1px solid #fde047' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Date</label>
                        <input
                          type="date"
                          value={payment.date}
                          onChange={(e) => updatePartialPayment(index, 'date', e.target.value)}
                          style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                        />
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Amount</label>
                        <input
                          type="number"
                          value={payment.amount}
                          onChange={(e) => updatePartialPayment(index, 'amount', parseFloat(e.target.value) || 0)}
                          style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                        />
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Mode</label>
                        <select
                          value={payment.payment_mode}
                          onChange={(e) => updatePartialPayment(index, 'payment_mode', e.target.value)}
                          style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                        >
                          {PAYMENT_MODES.map(mode => <option key={mode} value={mode}>{mode}</option>)}
                        </select>
                      </div>

                      <div style={{ gridColumn: 'span 2' }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '500', marginBottom: '0.25rem' }}>Check/Transaction Number</label>
                        <input
                          type="text"
                          value={payment.transaction_number || ''}
                          onChange={(e) => updatePartialPayment(index, 'transaction_number', e.target.value)}
                          placeholder="Optional"
                          style={{ width: '100%', padding: '0.375rem', border: '1px solid #d1d5db', borderRadius: '0.375rem', fontSize: '0.875rem' }}
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() => removePartialPayment(index)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', padding: '0.375rem' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Summary */}
          <div style={{ backgroundColor: '#f3f4f6', padding: '1.5rem', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', textAlign: 'center' }}>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Total Cost</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#dc2626' }}>₹{totalCost.toFixed(2)}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Profit</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: profit >= 0 ? '#16a34a' : '#dc2626' }}>₹{profit.toFixed(2)}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Margin</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#6366f1' }}>{profitMargin}%</div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onClose}
              style={{ padding: '0.75rem 1.5rem', backgroundColor: '#f3f4f6', color: '#374151', border: 'none', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ padding: '0.75rem 1.5rem', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500' }}
            >
              {revenue ? 'Update' : 'Save'} Revenue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RevenueFormEnhanced;
