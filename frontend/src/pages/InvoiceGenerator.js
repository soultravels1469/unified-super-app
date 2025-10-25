import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { FileText, Download } from 'lucide-react';

function InvoiceGenerator() {
  const [revenues, setRevenues] = useState([]);
  const [selectedRevenue, setSelectedRevenue] = useState('');
  const [invoiceData, setInvoiceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRevenues();
  }, []);

  const fetchRevenues = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const received = response.data.filter(r => r.status === 'Received' && r.received_amount > 0);
      setRevenues(received);
    } catch (error) {
      toast.error('Failed to load revenues');
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
    } catch (error) {
      toast.error('Failed to generate invoice');
    }
  };

  const handlePrintInvoice = () => {
    window.print();
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
          <div className="invoice-actions no-print" style={{ marginBottom: '1rem' }}>
            <button className="btn btn-success" onClick={handlePrintInvoice}>
              <Download size={16} style={{ marginRight: '0.5rem' }} />
              Print / Download PDF
            </button>
          </div>

          <div className="invoice-container" style={{
            background: 'white',
            padding: '3rem',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
          }}>
            <div style={{ borderBottom: '3px solid #6366f1', paddingBottom: '2rem', marginBottom: '2rem' }}>
              <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: '#6366f1', marginBottom: '0.5rem' }}>
                TAX INVOICE
              </h1>
              <div style={{ fontSize: '1.125rem', color: '#64748b' }}>Soul Immigration & Travels</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
              <div>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#1a202c' }}>Bill To:</div>
                <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>{invoiceData.client_name}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 600 }}>Invoice No:</span> {invoiceData.invoice_number}
                </div>
                <div>
                  <span style={{ fontWeight: 600 }}>Date:</span> {invoiceData.date}
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
                    {invoiceData.service_type} Services
                    <div style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.25rem' }}>
                      GST @ {invoiceData.gst_rate}%
                    </div>
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right', border: '1px solid #e2e8f0' }}>
                    ₹{invoiceData.taxable_amount?.toLocaleString()}
                  </td>
                </tr>
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div style={{ minWidth: '300px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
                  <span>Taxable Amount:</span>
                  <span style={{ fontWeight: 600 }}>₹{invoiceData.taxable_amount?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
                  <span>CGST @ {invoiceData.gst_rate / 2}%:</span>
                  <span style={{ fontWeight: 600 }}>₹{invoiceData.cgst?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
                  <span>SGST @ {invoiceData.gst_rate / 2}%:</span>
                  <span style={{ fontWeight: 600 }}>₹{invoiceData.sgst?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 0', background: '#f8fafc', paddingLeft: '1rem', paddingRight: '1rem', marginTop: '0.5rem', borderRadius: '8px' }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>Total Amount:</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#6366f1' }}>
                    ₹{invoiceData.total_amount?.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

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
