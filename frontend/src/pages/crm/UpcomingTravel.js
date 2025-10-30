import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Calendar, Eye } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL || '';

function UpcomingTravel() {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUpcomingTravels();
  }, []);

  const fetchUpcomingTravels = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/crm/upcoming-travels`);
      setLeads(response.data || []);
    } catch (error) {
      console.error('Error fetching upcoming travels:', error);
      toast.error('Failed to load upcoming travels');
    } finally {
      setLoading(false);
    }
  };

  const getDaysUntil = (date) => {
    const today = new Date();
    const travelDate = new Date(date);
    const diffTime = travelDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getDaysBadge = (days) => {
    if (days === 0) return 'bg-red-100 text-red-800';
    if (days === 1) return 'bg-orange-100 text-orange-800';
    if (days <= 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="page-container">
      <div className="flex items-center gap-3 mb-6">
        <Calendar size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>Upcoming Travel (Next 10 Days)</h1>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : leads.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No upcoming travels in the next 10 days</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {leads.map((lead) => {
            const daysUntil = getDaysUntil(lead.travel_date);
            return (
              <div key={lead._id} className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-lg">{lead.client_name}</h3>
                    <p className="text-sm text-gray-600">{lead.lead_id}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getDaysBadge(daysUntil)}`}>
                    {daysUntil === 0 ? 'Today!' : daysUntil === 1 ? 'Tomorrow' : `${daysUntil} days`}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <p><span className="text-gray-600">Type:</span> <span className="font-medium">{lead.lead_type}</span></p>
                  <p><span className="text-gray-600">Phone:</span> <span className="font-medium">{lead.primary_phone}</span></p>
                  <p><span className="text-gray-600">Travel Date:</span> <span className="font-medium">{new Date(lead.travel_date).toLocaleDateString()}</span></p>
                </div>
                <button
                  onClick={() => navigate(`/crm/leads/${lead._id}`)}
                  className="mt-4 w-full btn btn-primary btn-sm flex items-center justify-center gap-2"
                >
                  <Eye size={16} />
                  View Details
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default UpcomingTravel;
