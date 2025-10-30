import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { ListChecks, Plus, Search, Filter, Edit, Trash2, Eye, Phone, Mail } from 'lucide-react';
import { toast } from 'sonner';
import LeadForm from '@/components/crm/LeadForm';

const API = process.env.REACT_APP_BACKEND_URL || '';

function Leads() {
  const navigate = useNavigate();
  const location = useLocation();
  const role = localStorage.getItem('role');
  
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ total: 0, page: 1, pages: 1 });
  const [showModal, setShowModal] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    search: '',
    lead_type: '',
    status: '',
    source: ''
  });

  useEffect(() => {
    // Check if navigated from dashboard with filters
    if (location.state) {
      setFilters(prev => ({ ...prev, ...location.state }));
    }
    fetchLeads();
  }, [filters, pagination.page]);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const params = {
        skip: (pagination.page - 1) * 20,
        limit: 20,
        ...filters
      };
      
      const response = await axios.get(`${API}/api/crm/leads`, { params });
      setLeads(response.data.leads || []);
      setPagination({
        total: response.data.total || 0,
        page: response.data.page || 1,
        pages: response.data.pages || 1
      });
    } catch (error) {
      console.error('Error fetching leads:', error);
      toast.error('Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (leadId) => {
    if (!window.confirm('Are you sure you want to delete this lead?')) return;
    
    try {
      await axios.delete(`${API}/api/crm/leads/${leadId}`);
      toast.success('Lead deleted successfully');
      fetchLeads();
    } catch (error) {
      console.error('Error deleting lead:', error);
      toast.error('Failed to delete lead');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'New': 'bg-blue-100 text-blue-800',
      'In Process': 'bg-yellow-100 text-yellow-800',
      'Booked': 'bg-green-100 text-green-800',
      'Converted': 'bg-green-100 text-green-800',
      'Cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const clearFilters = () => {
    setFilters({ search: '', lead_type: '', status: '', source: '' });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleLeadSaved = () => {
    setShowModal(false);
    setEditingLead(null);
    fetchLeads();
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <ListChecks size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>Leads</h1>
        </div>
        {role === 'admin' && (
          <button
            onClick={() => {
              setEditingLead(null);
              setShowModal(true);
            }}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus size={20} />
            Add New Lead
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search */}
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Name, phone, email, or reference code"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Lead Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead Type</label>
            <select
              value={filters.lead_type}
              onChange={(e) => setFilters({ ...filters, lead_type: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="">All Types</option>
              <option value="Visa">Visa</option>
              <option value="Ticket">Ticket</option>
              <option value="Package">Package</option>
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="">All Status</option>
              <option value="New">New</option>
              <option value="In Process">In Process</option>
              <option value="Booked">Booked</option>
              <option value="Converted">Converted</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>

          {/* Source */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
            <select
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            >
              <option value="">All Sources</option>
              <option value="Instagram">Instagram</option>
              <option value="Referral">Referral</option>
              <option value="Walk-in">Walk-in</option>
              <option value="Website">Website</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>

        <div className="mt-3 flex gap-2">
          <button
            onClick={() => fetchLeads()}
            className="btn btn-primary btn-sm flex items-center gap-2"
          >
            <Filter size={16} />
            Apply Filters
          </button>
          <button
            onClick={clearFilters}
            className="btn btn-secondary btn-sm"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Leads List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : leads.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No leads found. Add your first lead to get started!</p>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lead ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Travel Date</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead) => (
                  <tr key={lead._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-600">
                      {lead.lead_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{lead.client_name}</div>
                      {lead.labels && lead.labels.length > 0 && (
                        <div className="flex gap-1 mt-1">
                          {lead.labels.map((label, idx) => (
                            <span key={idx} className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                              {label}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-1 text-sm text-gray-900">
                          <Phone size={14} />
                          {lead.primary_phone}
                        </div>
                        {lead.email && (
                          <div className="flex items-center gap-1 text-sm text-gray-500">
                            <Mail size={14} />
                            {lead.email}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {lead.lead_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(lead.status)}`}>
                        {lead.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {lead.source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {lead.travel_date ? new Date(lead.travel_date).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => navigate(`/crm/leads/${lead._id}`)}
                          className="text-indigo-600 hover:text-indigo-900"
                          title="View Details"
                        >
                          <Eye size={18} />
                        </button>
                        {role === 'admin' && (
                          <>
                            <button
                              onClick={() => {
                                setEditingLead(lead);
                                setShowModal(true);
                              }}
                              className="text-yellow-600 hover:text-yellow-900"
                              title="Edit"
                            >
                              <Edit size={18} />
                            </button>
                            <button
                              onClick={() => handleDelete(lead._id)}
                              className="text-red-600 hover:text-red-900"
                              title="Delete"
                            >
                              <Trash2 size={18} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex justify-between items-center mt-4">
              <div className="text-sm text-gray-700">
                Showing {(pagination.page - 1) * 20 + 1} to {Math.min(pagination.page * 20, pagination.total)} of {pagination.total} leads
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                  disabled={pagination.page === 1}
                  className="btn btn-secondary btn-sm"
                >
                  Previous
                </button>
                <span className="px-4 py-2 bg-white border rounded text-sm">
                  Page {pagination.page} of {pagination.pages}
                </span>
                <button
                  onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                  disabled={pagination.page === pagination.pages}
                  className="btn btn-secondary btn-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Lead Form Modal */}
      {showModal && (
        <LeadForm
          lead={editingLead}
          onClose={() => {
            setShowModal(false);
            setEditingLead(null);
          }}
          onSaved={handleLeadSaved}
        />
      )}
    </div>
  );
}

export default Leads;