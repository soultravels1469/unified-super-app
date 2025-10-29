import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { ScrollText } from 'lucide-react';

function ActivityLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/activity-logs?limit=200`);
      setLogs(response.data);
    } catch (error) {
      toast.error('Failed to load activity logs');
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action) => {
    switch(action) {
      case 'CREATE': return '#10b981';
      case 'UPDATE': return '#f59e0b';
      case 'DELETE': return '#ef4444';
      default: return '#64748b';
    }
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
  };

  if (loading) return <div className="page-container">Loading logs...</div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <ScrollText size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Activity Logs</h1>
      </div>

      <div className="card" style={{ padding: '1.5rem' }}>
        <p style={{ color: '#64748b', marginBottom: '1.5rem', fontSize: '0.875rem' }}>📋 View-only log of all system activities</p>
        
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {logs.map((log) => (
            <div key={log.id} style={{
              padding: '1rem',
              background: '#f9fafb',
              borderRadius: '8px',
              borderLeft: `4px solid ${getActionColor(log.action)}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '1rem', flexWrap: 'wrap' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <span style={{
                      background: getActionColor(log.action),
                      color: 'white',
                      padding: '0.125rem 0.5rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.75rem',
                      fontWeight: 600
                    }}>
                      {log.action}
                    </span>
                    <span style={{ fontSize: '0.875rem', color: '#64748b' }}>{log.module}</span>
                  </div>
                  <p style={{ margin: 0, color: '#1e293b' }}>{log.description}</p>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                  {formatDate(log.timestamp)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {logs.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
            No activity logs yet
          </div>
        )}
      </div>
    </div>
  );
}

export default ActivityLogs;