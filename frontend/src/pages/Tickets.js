import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth } from '@/utils/helpers';
import RevenueFormEnhanced from '../components/RevenueFormEnhanced';

function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingTicket, setEditingTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    try {
      const response = await axios.get(`${API}/revenue`);
      const filtered = response.data.filter(r => r.source === 'Ticket');
      setTickets(filtered);
    } catch (error) {
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this ticket?')) return;
    try {
      await axios.delete(`${API}/revenue/${id}`);
      toast.success('Ticket deleted successfully');
      fetchTickets();
    } catch (error) {
      toast.error('Failed to delete ticket');
    }
  };

  const handleEdit = (ticket) => {
    setEditingTicket(ticket);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingTicket(null);
    fetchTickets();
  };

  const groupedTickets = groupByMonth(tickets);

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="tickets-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>Tickets</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.5rem' }}>
            ℹ️ Entries are auto-generated from the Revenue module
          </p>
        </div>
      </div>

      {showForm && (
        <RevenueFormEnhanced
          revenue={editingTicket}
          onClose={handleFormClose}
          defaultSource="Ticket"
        />
      )}

      {Object.keys(groupedTickets).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No tickets yet. Tickets are created automatically through the Revenue module.
        </div>
      ) : (
        Object.entries(groupedTickets).reverse().map(([month, items]) => (
          <div key={month} className="month-section" data-testid={`month-${month}`}>
            <h2 className="month-title">{month}</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Client Name</th>
                  <th>Sale Price</th>
                  <th>Cost</th>
                  <th>Profit</th>
                  <th>Received</th>
                  <th>Pending</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((ticket) => (
                  <tr key={ticket.id}>
                    <td>{ticket.date}</td>
                    <td>{ticket.client_name}</td>
                    <td>₹{(ticket.sale_price || 0).toLocaleString()}</td>
                    <td>₹{(ticket.total_cost_price || 0).toLocaleString()}</td>
                    <td style={{ color: ticket.profit >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      ₹{(ticket.profit || 0).toLocaleString()}
                    </td>
                    <td>₹{ticket.received_amount.toLocaleString()}</td>
                    <td>₹{ticket.pending_amount.toLocaleString()}</td>
                    <td>
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        borderRadius: '9999px',
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        background: ticket.status === 'Completed' ? '#d1fae5' : '#fed7aa',
                        color: ticket.status === 'Completed' ? '#065f46' : '#9a3412'
                      }}>
                        {ticket.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleEdit(ticket)}
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.75rem' }}
                          data-testid={`edit-ticket-${ticket.id}`}
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(ticket.id)}
                          className="btn"
                          style={{ padding: '0.25rem 0.75rem', background: '#ef4444', color: 'white' }}
                          data-testid={`delete-ticket-${ticket.id}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}

export default Tickets;