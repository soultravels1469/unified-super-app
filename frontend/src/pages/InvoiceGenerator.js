import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { FileText, Download, Edit2, Save } from 'lucide-react';
import jsPDF from 'jspdf';

function InvoiceGenerator() {
  const [revenues, setRevenues] = useState([]);
  const [selectedRevenue, setSelectedRevenue] = useState('');
  const [invoiceData, setInvoiceData] = useState(null);
  const [adminSettings, setAdminSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editableData, setEditableData] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [revenuesRes, settingsRes] = await Promise.all([
        axios.get(`${API}/revenue`),
        axios.get(`${API}/admin/settings`)
      ]);
      const received = revenuesRes.data.filter(r => r.status === 'Received' && r.received_amount > 0);
      setRevenues(received);
      setAdminSettings(settingsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInvoice = async () => {
    if (!selectedRevenue) {
      toast.error('Please select a revenue entry');
      return;
    }

    try {
      const response = await axios.get(`${API}/accounting/gst-invoice/${selectedRevenue}`);
      setInvoiceData(response.data);
      setEditableData(response.data);
      setIsEditing(false);
    } catch (error) {
      toast.error('Failed to generate invoice');
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    setInvoiceData(editableData);
    setIsEditing(false);
    toast.success('Invoice updated');
  };

  const handleDownloadPDF = () => {
    const doc = new jsPDF();
    const data = isEditing ? editableData : invoiceData;
    
    // Company Header
    doc.setFontSize(24);
    doc.setFont(undefined, 'bold');
    doc.text(adminSettings?.company_name || 'Soul Immigration & Travels', 20, 20);
    
    // Invoice Title
    doc.setFontSize(18);
    doc.text('TAX INVOICE', 150, 20);
    
    // Company Details
    doc.setFontSize(10);
    doc.setFont(undefined, 'normal');
    if (adminSettings?.address) doc.text(adminSettings.address, 20, 30);
    if (adminSettings?.phone) doc.text(`Phone: ${adminSettings.phone}`, 20, 35);
    if (adminSettings?.email) doc.text(`Email: ${adminSettings.email}`, 20, 40);
    if (adminSettings?.gstin) doc.text(`GSTIN: ${adminSettings.gstin}`, 20, 45);
    
    // Invoice Details
    doc.text(`Invoice No: ${data.invoice_number}`, 150, 30);
    doc.text(`Date: ${data.date}`, 150, 35);
    
    // Bill To
    doc.setFont(undefined, 'bold');
    doc.text('Bill To:', 20, 60);
    doc.setFont(undefined, 'normal');
    doc.text(data.client_name, 20, 65);
    
    // Table
    doc.setFont(undefined, 'bold');
    doc.text('Description', 20, 85);
    doc.text('Amount', 170, 85);
    doc.line(20, 87, 190, 87);
    
    doc.setFont(undefined, 'normal');
    doc.text(`${data.service_type} Services`, 20, 95);
    doc.text(`₹${data.taxable_amount?.toLocaleString()}`, 170, 95);
    
    // GST Breakdown
    doc.line(20, 100, 190, 100);
    doc.text(`CGST @ ${data.gst_rate / 2}%`, 20, 108);
    doc.text(`₹${data.cgst?.toLocaleString()}`, 170, 108);
    doc.text(`SGST @ ${data.gst_rate / 2}%`, 20, 115);
    doc.text(`₹${data.sgst?.toLocaleString()}`, 170, 115);
    
    // Total
    doc.line(20, 120, 190, 120);
    doc.setFont(undefined, 'bold');
    doc.setFontSize(12);
    doc.text('Total Amount', 20, 128);
    doc.text(`₹${data.total_amount?.toLocaleString()}`, 170, 128);
    
    // Bank Details
    if (adminSettings?.bank_name) {
      doc.setFontSize(10);
      doc.setFont(undefined, 'bold');
      doc.text('Bank Details:', 20, 150);
      doc.setFont(undefined, 'normal');
      doc.text(`Bank: ${adminSettings.bank_name}`, 20, 155);
      if (adminSettings.account_number) doc.text(`Account: ${adminSettings.account_number}`, 20, 160);
      if (adminSettings.ifsc_code) doc.text(`IFSC: ${adminSettings.ifsc_code}`, 20, 165);
      if (adminSettings.branch) doc.text(`Branch: ${adminSettings.branch}`, 20, 170);
    }
    
    // Footer
    doc.setFontSize(8);
    doc.text('This is a computer-generated invoice and does not require a signature.', 20, 280);
    
    doc.save(`Invoice_${data.invoice_number}.pdf`);
    toast.success('Invoice downloaded successfully!');
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="invoice-generator-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <FileText size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>GST Invoice Generator</h1>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Select Revenue Entry</label>
            <select
              value={selectedRevenue}
              onChange={(e) => setSelectedRevenue(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '12px',
                border: '2px solid #e2e8f0',
                fontSize: '0.9375rem'
              }}
            >
              <option value="">-- Select --</option>
              {revenues.map(rev => (
                <option key={rev.id} value={rev.id}>
                  {rev.date} - {rev.client_name} - ₹{rev.received_amount.toLocaleString()} ({rev.source})
                </option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary" onClick={handleGenerateInvoice}>
            Generate Invoice
          </button>
        </div>
      </div>

      {invoiceData && (
        <>
          <div className="invoice-actions no-print" style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
            {!isEditing && (
              <button className="btn btn-secondary" onClick={handleEdit}>
                <Edit2 size={16} style={{ marginRight: '0.5rem' }} />
                Edit Invoice
              </button>
            )}
            {isEditing && (
              <button className="btn btn-primary" onClick={handleSaveEdit}>
                <Save size={16} style={{ marginRight: '0.5rem' }} />
                Save Changes
              </button>
            )}
            <button className="btn btn-success" onClick={handleDownloadPDF}>
              <Download size={16} style={{ marginRight: '0.5rem' }} />
              Download PDF
            </button>
          </div>

          <div className="invoice-container" style={{
            background: 'white',
            padding: '3rem',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
          }}>
            <div style={{ borderBottom: '3px solid #6366f1', paddingBottom: '2rem', marginBottom: '2rem' }}>
              {adminSettings?.logo_url && (
                <img src={adminSettings.logo_url} alt="Company Logo" style={{ height: '60px', marginBottom: '1rem' }} />
              )}
              <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: '#6366f1', marginBottom: '0.5rem' }}>
                TAX INVOICE
              </h1>
              <div style={{ fontSize: '1.125rem', color: '#64748b' }}>{adminSettings?.company_name || 'Soul Immigration & Travels'}</div>
              {adminSettings?.address && <div style={{ fontSize: '0.875rem', color: '#64748b' }}>{adminSettings.address}</div>}
              {adminSettings?.gstin && <div style={{ fontSize: '0.875rem', color: '#64748b' }}>GSTIN: {adminSettings.gstin}</div>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
              <div>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#1a202c' }}>Bill To:</div>
                {isEditing ? (
                  <input
                    type="text"
                    value={editableData.client_name}
                    onChange={(e) => setEditableData({ ...editableData, client_name: e.target.value })}
                    style={{ fontSize: '1.125rem', fontWeight: 600, width: '100%', padding: '0.5rem', border: '2px solid #e2e8f0', borderRadius: '8px' }}
                  />
                ) : (
                  <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>{invoiceData.client_name}</div>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 600 }}>Invoice No:</span> {isEditing ? (
                    <input
                      type="text"
                      value={editableData.invoice_number}
                      onChange={(e) => setEditableData({ ...editableData, invoice_number: e.target.value })}
                      style={{ width: '150px', padding: '0.25rem', border: '2px solid #e2e8f0', borderRadius: '4px' }}
                    />
                  ) : invoiceData.invoice_number}
                </div>
                <div>
                  <span style={{ fontWeight: 600 }}>Date:</span> {isEditing ? (
                    <input
                      type="date"
                      value={editableData.date}
                      onChange={(e) => setEditableData({ ...editableData, date: e.target.value })}
                      style={{ width: '150px', padding: '0.25rem', border: '2px solid #e2e8f0', borderRadius: '4px' }}
                    />
                  ) : invoiceData.date}
                </div>
              </div>
            </div>

            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              marginBottom: '2rem',
              border: '1px solid #e2e8f0'
            }}>
              <thead style={{ background: '#f8fafc' }}>
                <tr>
                  <th style={{ padding: '1rem', textAlign: 'left', border: '1px solid #e2e8f0' }}>Service Description</th>
                  <th style={{ padding: '1rem', textAlign: 'right', border: '1px solid #e2e8f0' }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ padding: '1rem', border: '1px solid #e2e8f0' }}>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editableData.service_type}
                        onChange={(e) => setEditableData({ ...editableData, service_type: e.target.value })}
                        style={{ width: '100%', padding: '0.5rem', border: '2px solid #e2e8f0', borderRadius: '4px' }}
                      />
                    ) : invoiceData.service_type} Services
                    <div style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.25rem' }}>
                      GST @ {isEditing ? editableData.gst_rate : invoiceData.gst_rate}%
                    </div>
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right', border: '1px solid #e2e8f0' }}>
                    ₹{(isEditing ? editableData.taxable_amount : invoiceData.taxable_amount)?.toLocaleString()}
                  </td>
                </tr>
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div style={{ minWidth: '300px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
                  <span>Taxable Amount:</span>
                  <span style={{ fontWeight: 600 }}>₹{(isEditing ? editableData.taxable_amount : invoiceData.taxable_amount)?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
                  <span>CGST @ {(isEditing ? editableData.gst_rate : invoiceData.gst_rate) / 2}%:</span>
                  <span style={{ fontWeight: 600 }}>₹{(isEditing ? editableData.cgst : invoiceData.cgst)?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
                  <span>SGST @ {(isEditing ? editableData.gst_rate : invoiceData.gst_rate) / 2}%:</span>
                  <span style={{ fontWeight: 600 }}>₹{(isEditing ? editableData.sgst : invoiceData.sgst)?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 0', background: '#f8fafc', paddingLeft: '1rem', paddingRight: '1rem', marginTop: '0.5rem', borderRadius: '8px' }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>Total Amount:</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#6366f1' }}>
                    ₹{(isEditing ? editableData.total_amount : invoiceData.total_amount)?.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {adminSettings?.bank_name && (
              <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '2px solid #e2e8f0' }}>
                <h4 style={{ fontWeight: 600, marginBottom: '1rem' }}>Bank Details</h4>
                <div style={{ fontSize: '0.9375rem', color: '#475569' }}>
                  <div>Bank Name: {adminSettings.bank_name}</div>
                  {adminSettings.account_number && <div>Account Number: {adminSettings.account_number}</div>}
                  {adminSettings.ifsc_code && <div>IFSC Code: {adminSettings.ifsc_code}</div>}
                  {adminSettings.branch && <div>Branch: {adminSettings.branch}</div>}
                </div>
              </div>
            )}

            <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '2px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                <p><strong>Terms & Conditions:</strong></p>
                <p>This is a computer-generated invoice and does not require a signature.</p>
                <p>Payment due within 30 days of invoice date.</p>
              </div>
            </div>
          </div>
        </>
      )}

      <style jsx>{`
        @media print {
          .no-print {
            display: none !important;
          }
          
          .page-container {
            padding: 0 !important;
          }
          
          .invoice-container {
            box-shadow: none !important;
          }
        }
      `}</style>
    </div>
  );
}

export default InvoiceGenerator;
