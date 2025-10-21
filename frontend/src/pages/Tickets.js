import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import RevenueForm from '@/components/RevenueForm';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth } from '@/utils/helpers';

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
        <h1 className="page-title" style={{ margin: 0 }}>Tickets</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)} data-testid="add-ticket-button">
          + Add Ticket
        </button>
      </div>

      {showForm && (
        <RevenueForm
          revenue={editingTicket}
          onClose={handleFormClose}
          defaultSource="Ticket"
        />
      )}

      {Object.keys(groupedTickets).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No tickets yet. Add your first ticket!
        </div>
      ) : (
        Object.entries(groupedTickets).reverse().map(([month, items]) => (
          <div key={month} className="month-section" data-testid={`month-${month}`}>
            <h3 className="month-title">{new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Client Name</th>
                    <th>Payment Mode</th>
                    <th>Received</th>
                    <th>Pending</th>
                    <th>Status</th>
                    <th>Supplier</th>
                    <th>Notes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>{ticket.date}</td>
                      <td>{ticket.client_name}</td>
                      <td>{ticket.payment_mode}</td>
                      <td>₹{ticket.received_amount.toLocaleString()}</td>
                      <td>₹{ticket.pending_amount.toLocaleString()}</td>
                      <td>
                        <span className={`status-badge status-${ticket.status.toLowerCase()}`}>
                          {ticket.status}
                        </span>
                      </td>
                      <td>{ticket.supplier || '-'}</td>
                      <td>{ticket.notes || '-'}</td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(ticket)}>
                            <Pencil size={16} />
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(ticket.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}

      <style jsx>{`
        .month-section {
          margin-bottom: 2.5rem;
        }

        .month-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #1a202c;
          margin-bottom: 1rem;
          padding-left: 0.5rem;
          border-left: 4px solid #6366f1;
        }
      `}</style>
    </div>
  );
}

export default Tickets;
