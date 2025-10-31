import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';

const API = process.env.REACT_APP_API_URL || 'https://backend-mwh2.onrender.com';

function CRMReports() {
  const [monthlyLeads, setMonthlyLeads] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const year = new Date().getFullYear();
      const [monthlyRes, leaderboardRes] = await Promise.all([
        axios.get(`${API}/api/crm/reports/monthly?year=${year}`),
        axios.get(`${API}/api/crm/reports/referral-leaderboard`)
      ]);
      setMonthlyLeads(monthlyRes.data);
      setLeaderboard(leaderboardRes.data);
    } catch (error) {
      console.error('Error fetching reports:', error);
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
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

  return (
    <div className="page-container">
      <div className="flex items-center gap-3 mb-6">
        <TrendingUp size={32} style={{ color: '#6366f1' }} />
        <h1 className="page-title" style={{ margin: 0 }}>CRM Reports</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Monthly Leads</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyLeads}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#6366f1" name="Leads" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Top Referrers</h3>
          {leaderboard.length > 0 ? (
            <div className="space-y-2">
              {leaderboard.map((referrer, index) => (
                <div key={referrer._id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-lg text-indigo-600">#{index + 1}</span>
                    <div>
                      <p className="font-medium">{referrer.client_name}</p>
                      <p className="text-xs text-gray-500">Code: {referrer.referral_code}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">{referrer.referral_count} referrals</p>
                    <p className="text-xs text-gray-500">{referrer.loyalty_points} points</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No referral data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default CRMReports;
