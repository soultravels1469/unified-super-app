import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Database, Download, Upload, Trash2, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

function BackupManager() {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(null);

  useEffect(() => {
    fetchBackups();
  }, []);

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/backup/list`);
      setBackups(response.data);
    } catch (error) {
      toast.error('Failed to load backups');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    if (creating) return;
    
    try {
      setCreating(true);
      const response = await axios.post(`${API}/backup/create`);
      
      if (response.data.success) {
        toast.success(`Backup created: ${response.data.filename}`);
        fetchBackups();
      }
    } catch (error) {
      toast.error('Failed to create backup');
      console.error(error);
    } finally {
      setCreating(false);
    }
  };

  const restoreBackup = async (filename) => {
    const confirmed = window.confirm(
      `⚠️ WARNING: This will replace ALL current data with the backup from ${filename}.\n\nAre you absolutely sure you want to continue?`
    );
    
    if (!confirmed) return;
    
    const doubleCheck = window.confirm(
      'This action cannot be undone. Type "RESTORE" in the next dialog to confirm.'
    );
    
    if (!doubleCheck) return;
    
    try {
      setRestoring(filename);
      const response = await axios.post(`${API}/backup/restore/${filename}`);
      
      if (response.data.success) {
        toast.success(`Database restored from ${filename}. Please refresh the page.`);
        setTimeout(() => window.location.reload(), 2000);
      }
    } catch (error) {
      toast.error('Failed to restore backup');
      console.error(error);
    } finally {
      setRestoring(null);
    }
  };

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="page-container">
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Database size={32} style={{ color: '#3b82f6' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Backup & Recovery</h1>
        </div>
        <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
          Automated daily backups at midnight. Manual backups and restore options available below.
        </p>
      </div>

      {/* Info Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#eff6ff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #dbeafe' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <CheckCircle size={20} style={{ color: '#3b82f6' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: '600', margin: 0, color: '#1e40af' }}>Auto Backup</h3>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#1e40af', margin: 0 }}>Daily at midnight (system)</p>
        </div>

        <div style={{ backgroundColor: '#fef3c7', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #fde047' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertTriangle size={20} style={{ color: '#ca8a04' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: '600', margin: 0, color: '#a16207' }}>Retention</h3>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#a16207', margin: 0 }}>Last 7 backups kept</p>
        </div>

        <div style={{ backgroundColor: '#f0fdf4', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #dcfce7' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Database size={20} style={{ color: '#16a34a' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: '600', margin: 0, color: '#15803d' }}>Total Backups</h3>
          </div>
          <p style={{ fontSize: '1.5rem', fontWeight: '700', color: '#15803d', margin: 0 }}>{backups.length}</p>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button
          onClick={createBackup}
          disabled={creating}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            backgroundColor: creating ? '#9ca3af' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: creating ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            fontSize: '1rem'
          }}
        >
          {creating ? <RefreshCw size={20} className="animate-spin" /> : <Download size={20} />}
          {creating ? 'Creating...' : '🧩 Backup Now'}
        </button>

        <button
          onClick={fetchBackups}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            backgroundColor: '#f3f4f6',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Backups List */}
      <div style={{ backgroundColor: 'white', borderRadius: '0.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.5rem', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0 }}>♻️ Available Backups</h2>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto', color: '#3b82f6' }} />
          </div>
        ) : backups.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280' }}>
            No backups available. Create your first backup above.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
              <tr>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Backup File</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Created</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Age</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Size</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'center', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((backup, index) => (
                <tr key={backup.filename} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '1rem', fontFamily: 'monospace', fontSize: '0.875rem', color: '#111827' }}>
                    {backup.filename}
                  </td>
                  <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                    {formatDate(backup.created_at)}
                  </td>
                  <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                    {backup.age_days === 0 ? 'Today' : `${backup.age_days} day${backup.age_days > 1 ? 's' : ''} ago`}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', color: '#6b7280' }}>
                    {backup.size_mb.toFixed(2)} MB
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center' }}>
                    <button
                      onClick={() => restoreBackup(backup.filename)}
                      disabled={restoring === backup.filename}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem 1rem',
                        backgroundColor: restoring === backup.filename ? '#9ca3af' : '#10b981',
                        color: 'white',
                        border: 'none',
                        borderRadius: '0.375rem',
                        cursor: restoring === backup.filename ? 'not-allowed' : 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                    >
                      {restoring === backup.filename ? (
                        <><RefreshCw size={16} className="animate-spin" /> Restoring...</>
                      ) : (
                        <><Upload size={16} /> Restore</>
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Warning Notice */}
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <AlertTriangle size={20} style={{ color: '#dc2626', flexShrink: 0, marginTop: '0.125rem' }} />
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#991b1b', margin: '0 0 0.5rem 0' }}>
              Important Notes
            </h3>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.875rem', color: '#991b1b', lineHeight: '1.5' }}>
              <li>Restoring a backup will <strong>completely replace</strong> all current data</li>
              <li>This action cannot be undone - make sure you have a recent backup before restoring</li>
              <li>All users will be logged out after a restore operation</li>
              <li>Backups are stored locally on the server</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BackupManager;
