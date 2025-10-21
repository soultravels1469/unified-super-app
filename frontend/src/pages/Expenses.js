import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import ExpenseForm from '@/components/ExpenseForm';
import { Pencil, Trash2 } from 'lucide-react';
import { groupByMonth, getAvailableMonths } from '@/utils/helpers';

function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState('all');

  useEffect(() => {
    fetchExpenses();
  }, []);

  const fetchExpenses = async () => {
    try {
      const response = await axios.get(`${API}/expenses`);
      setExpenses(response.data);
    } catch (error) {
      toast.error('Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) return;

    try {
      await axios.delete(`${API}/expenses/${id}`);
      toast.success('Expense deleted successfully');
      fetchExpenses();
    } catch (error) {
      toast.error('Failed to delete expense');
    }
  };

  const handleEdit = (expense) => {
    setEditingExpense(expense);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingExpense(null);
    fetchExpenses();
  };

  const availableMonths = getAvailableMonths(expenses);
  const groupedExpenses = groupByMonth(expenses);
  
  const filteredMonths = selectedMonth === 'all' 
    ? Object.entries(groupedExpenses)
    : [[selectedMonth, groupedExpenses[selectedMonth] || []]];

  if (loading) {
    return <div className="page-container">Loading...</div>;
  }

  return (
    <div className="page-container" data-testid="expenses-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="page-title" style={{ margin: 0 }} data-testid="expenses-title">Expense Tracker</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)} data-testid="add-expense-button">
          + Add Expense
        </button>
      </div>

      {availableMonths.length > 0 && (
        <div className="filter-section" style={{ marginBottom: '2rem' }}>
          <label style={{ marginRight: '1rem', fontWeight: 500, color: '#475569' }}>Filter by Month:</label>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="month-filter"
            style={{
              padding: '0.625rem 1rem',
              borderRadius: '12px',
              border: '2px solid #e2e8f0',
              fontSize: '0.9375rem',
              minWidth: '200px'
            }}
          >
            <option value="all">All Months</option>
            {availableMonths.map(month => (
              <option key={month} value={month}>
                {new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}
              </option>
            ))}
          </select>
        </div>
      )}

      {showForm && (
        <ExpenseForm
          expense={editingExpense}
          onClose={handleFormClose}
        />
      )}

      {expenses.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No expense entries yet. Add your first entry!
        </div>
      ) : filteredMonths.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          No expenses for the selected month.
        </div>
      ) : (
        filteredMonths.reverse().map(([month, items]) => (
          items && items.length > 0 && (
            <div key={month} className="month-section">
              <h3 className="month-title">{new Date(month + '-01').toLocaleDateString('default', { month: 'long', year: 'numeric' })}</h3>
              <div className="table-container" data-testid="expenses-table">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Category</th>
                      <th>Payment Mode</th>
                      <th>Amount</th>
                      <th>Description</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((exp) => (
                      <tr key={exp.id} data-testid={`expense-row-${exp.id}`}>
                        <td>{exp.date}</td>
                        <td>{exp.category}</td>
                        <td>{exp.payment_mode}</td>
                        <td>₹{exp.amount.toLocaleString()}</td>
                        <td>{exp.description || '-'}</td>
                        <td>
                          <div className="actions">
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleEdit(exp)}
                              data-testid={`edit-expense-${exp.id}`}
                            >
                              <Pencil size={16} />
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleDelete(exp.id)}
                              data-testid={`delete-expense-${exp.id}`}
                            >
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
          )
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

export default Expenses;
