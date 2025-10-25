import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { toast } from 'sonner';
import { Users, Plus, Trash2, Key } from 'lucide-react';

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'viewer' });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data.users);
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();

    if (newUser.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    try {
      await axios.post(`${API}/admin/users`, newUser);
      toast.success('User created successfully!');
      setShowAddUser(false);
      setNewUser({ username: '', password: '', role: 'viewer' });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleDeleteUser = async (username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) return;

    try {
      await axios.delete(`${API}/admin/users/${username}`);
      toast.success('User deleted successfully');
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleResetPassword = async (username) => {
    const newPassword = prompt(`Enter new password for "${username}":`);
    if (!newPassword) return;

    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    try {
      await axios.put(`${API}/admin/users/${username}/password`, { new_password: newPassword });
      toast.success('Password updated successfully');
    } catch (error) {
      toast.error('Failed to update password');
    }
  };

  if (loading) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container" data-testid="user-management-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Users size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>User Management</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddUser(true)}>
          <Plus size={18} style={{ marginRight: '0.5rem' }} />
          Add User
        </button>
      </div>

      {showAddUser && (
        <div className="card" style={{ marginBottom: '2rem', padding: '2rem', background: '#f8fafc' }}>
          <h3 style={{ marginBottom: '1.5rem', fontSize: '1.125rem', fontWeight: 600 }}>Create New User</h3>
          <form onSubmit={handleAddUser}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Username *</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Password *</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  required
                  minLength="6"
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Role *</label>
                <select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer (CA)</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="submit" className="btn btn-primary btn-sm">Create User</button>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowAddUser(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Role</th>
              <th>Created At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id}>
                  <td style={{ fontWeight: 600 }}>{user.username}</td>
                  <td>
                    <span style={{
                      padding: '0.375rem 0.875rem',
                      borderRadius: '20px',
                      fontSize: '0.8125rem',
                      fontWeight: 500,
                      background: user.role === 'admin' ? '#dbeafe' : '#fef3c7',
                      color: user.role === 'admin' ? '#1e40af' : '#92400e'
                    }}>
                      {user.role === 'admin' ? 'Admin' : 'Viewer'}
                    </span>
                  </td>
                  <td>{new Date(user.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="actions">
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleResetPassword(user.username)}
                        title="Reset Password"
                      >
                        <Key size={16} />
                      </button>
                      {user.username !== 'admin' && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDeleteUser(user.username)}
                          title="Delete User"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: '2rem', padding: '1.5rem', background: '#eff6ff' }}>
        <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#1e40af', marginBottom: '0.75rem' }}>Default Credentials</h4>
        <div style={{ fontSize: '0.875rem', color: '#1e3a8a' }}>
          <p><strong>Admin:</strong> username: admin, password: admin123</p>
          <p><strong>Viewer (CA):</strong> username: viewer, password: viewer123</p>
        </div>
      </div>
    </div>
  );
}

export default UserManagement;
