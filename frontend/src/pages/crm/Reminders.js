import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bell, Plus, Check, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL || '';

function Reminders() {
  const role = localStorage.getItem('role');
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ title: '', description: '', date: '', priority: 'Medium' });

  useEffect(() => {
    fetchReminders();
  }, []);

  const fetchReminders = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/crm/reminders`);
      setReminders(response.data || []);
    } catch (error) {
      console.error('Error fetching reminders:', error);
      toast.error('Failed to load reminders');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/api/crm/reminders`, { ...formData, date: new Date(formData.date).toISOString() });
      toast.success('Reminder created');
      setShowModal(false);
      setFormData({ title: '', description: '', date: '', priority: 'Medium' });
      fetchReminders();
    } catch (error) {
      toast.error('Failed to create reminder');
    }
  };

  const handleMarkDone = async (id) => {
    try {
      await axios.put(`${API}/api/crm/reminders/${id}`, { status: 'Done' });
      toast.success('Reminder marked as done');
      fetchReminders();
    } catch (error) {
      toast.error('Failed to update reminder');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this reminder?')) return;
    try {
      await axios.delete(`${API}/api/crm/reminders/${id}`);
      toast.success('Reminder deleted');
      fetchReminders();
    } catch (error) {
      toast.error('Failed to delete reminder');
    }
  };

  const getPriorityColor = (priority) => {
    const colors = { Low: 'bg-gray-100 text-gray-800', Medium: 'bg-blue-100 text-blue-800', High: 'bg-red-100 text-red-800' };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="page-container">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <Bell size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Reminders</h1>
        </div>
        {role === 'admin' && (
          <button onClick={() => setShowModal(true)} className="btn btn-primary flex items-center gap-2">
            <Plus size={20} />
            Add Reminder
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="space-y-3">
          {reminders.filter(r => r.status === 'Pending').map((reminder) => (
            <div key={reminder._id} className="bg-white rounded-lg shadow p-4 flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold">{reminder.title}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getPriorityColor(reminder.priority)}`}>
                    {reminder.priority}
                  </span>
                </div>
                {reminder.description && <p className="text-sm text-gray-600 mb-1">{reminder.description}</p>}
                <p className="text-xs text-gray-500">{new Date(reminder.date).toLocaleString()}</p>
              </div>
              {role === 'admin' && (
                <div className="flex gap-2">
                  <button onClick={() => handleMarkDone(reminder._id)} className="text-green-600 hover:text-green-800" title="Mark Done">
                    <Check size={20} />
                  </button>
                  <button onClick={() => handleDelete(reminder._id)} className="text-red-600 hover:text-red-800" title="Delete">
                    <Trash2 size={20} />
                  </button>
                </div>
              )}
            </div>
          ))}
          {reminders.filter(r => r.status === 'Pending').length === 0 && (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">No pending reminders</p>
            </div>
          )}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Add Reminder</h2>
            <form onSubmit={handleCreate}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Title *</label>
                  <input type="text" value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})} className="w-full rounded-md border-gray-300" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} className="w-full rounded-md border-gray-300" rows={3} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Date & Time *</label>
                  <input type="datetime-local" value={formData.date} onChange={(e) => setFormData({...formData, date: e.target.value})} className="w-full rounded-md border-gray-300" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Priority</label>
                  <select value={formData.priority} onChange={(e) => setFormData({...formData, priority: e.target.value})} className="w-full rounded-md border-gray-300">
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reminders;
