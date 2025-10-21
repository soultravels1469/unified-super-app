import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import ExpenseForm from '@/components/ExpenseForm';
import { Pencil, Trash2 } from 'lucide-react';

function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [loading, setLoading] = useState(true);

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

      {showForm && (
        <ExpenseForm
          expense={editingExpense}
          onClose={handleFormClose}
        />
      )}

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
            {expenses.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No expense entries yet. Add your first entry!
                </td>
              </tr>
            ) : (
              expenses.map((exp) => (
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Expenses;
