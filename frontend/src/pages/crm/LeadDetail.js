import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Edit, Phone, Mail, Calendar, Tag, FileText } from 'lucide-react';
import { toast } from 'sonner';
import LeadForm from '@/components/crm/LeadForm';

const API = process.env.REACT_APP_API_URL || 'https://unified-super-app-5.onrender.com';

function LeadDetail() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const role = localStorage.getItem('role');
  const [lead, setLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    fetchLead();
  }, [leadId]);

  const fetchLead = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/crm/leads/${leadId}`);
      setLead(response.data);
    } catch (error) {
      console.error('Error fetching lead:', error);
      toast.error('Failed to load lead details');
      navigate('/crm/leads');
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <div className="page-container">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  if (!lead) return null;

  return (
    <div className="page-container">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/crm/leads')} className="text-gray-600 hover:text-gray-900">
            <ArrowLeft size={24} />
          </button>
          <h1 className="page-title" style={{ margin: 0 }}>Lead Details</h1>
        </div>
        {role === 'admin' && (
          <button onClick={() => setShowEditModal(true)} className="btn btn-primary flex items-center gap-2">
            <Edit size={18} />
            Edit Lead
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Client Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600">Lead ID</label>
                <p className="font-medium text-indigo-600">{lead.lead_id}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Client Name</label>
                <p className="font-medium">{lead.client_name}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Primary Phone</label>
                <p className="font-medium flex items-center gap-1">
                  <Phone size={16} />
                  {lead.primary_phone}
                </p>
              </div>
              {lead.alternate_phone && (
                <div>
                  <label className="text-sm text-gray-600">Alternate Phone</label>
                  <p className="font-medium">{lead.alternate_phone}</p>
                </div>
              )}
              {lead.email && (
                <div>
                  <label className="text-sm text-gray-600">Email</label>
                  <p className="font-medium flex items-center gap-1">
                    <Mail size={16} />
                    {lead.email}
                  </p>
                </div>
              )}
            </div>
          </div>

          {lead.notes && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <FileText size={20} />
                Notes
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap">{lead.notes}</p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Lead Details</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Status</label>
                <p className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(lead.status)}`}>
                  {lead.status}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Type</label>
                <p className="font-medium">{lead.lead_type}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Source</label>
                <p className="font-medium">{lead.source}</p>
              </div>
              {lead.travel_date && (
                <div>
                  <label className="text-sm text-gray-600">Travel Date</label>
                  <p className="font-medium flex items-center gap-1">
                    <Calendar size={16} />
                    {new Date(lead.travel_date).toLocaleDateString()}
                  </p>
                </div>
              )}
              {lead.labels && lead.labels.length > 0 && (
                <div>
                  <label className="text-sm text-gray-600 flex items-center gap-1">
                    <Tag size={16} />
                    Labels
                  </label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {lead.labels.map((label, idx) => (
                      <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-sm">
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Referral Info</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Referral Code</label>
                <p className="font-medium font-mono">{lead.referral_code}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Loyalty Points</label>
                <p className="font-medium text-green-600">{lead.loyalty_points || 0}</p>
              </div>
              <div>
                <label className="text-sm text-gray-600">Referred Clients</label>
                <p className="font-medium">{lead.referred_clients?.length || 0}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showEditModal && (
        <LeadForm
          lead={lead}
          onClose={() => setShowEditModal(false)}
          onSaved={() => {
            setShowEditModal(false);
            fetchLead();
          }}
        />
      )}
    </div>
  );
}

export default LeadDetail;
