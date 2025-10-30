import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { BarChart3, Users, UserCheck, Calendar, Bell, GitBranch, TrendingUp, Plus } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toast } from 'react-hot-toast';

const API = process.env.REACT_APP_BACKEND_URL || '';

function CRMDashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [monthlyLeads, setMonthlyLeads] = useState([]);
  const [leadTypeBreakdown, setLeadTypeBreakdown] = useState([]);
  const [leadSourceBreakdown, setLeadSourceBreakdown] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const year = new Date().getFullYear();

      const [summaryRes, monthlyRes, typeRes, sourceRes] = await Promise.all([
        axios.get(`${API}/api/crm/dashboard-summary`),
        axios.get(`${API}/api/crm/reports/monthly?year=${year}`),
        axios.get(`${API}/api/crm/reports/lead-type-breakdown`),
        axios.get(`${API}/api/crm/reports/lead-source-breakdown`)
      ]);

      setSummary(summaryRes.data);
      setMonthlyLeads(monthlyRes.data);
      setLeadTypeBreakdown(typeRes.data);
      setLeadSourceBreakdown(sourceRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (filter) => {
    navigate('/crm/leads', { state: filter });
  };

  const cards = [
    {
      title: 'Total Leads',
      value: summary?.total_leads || 0,
      icon: Users,
      color: '#6366f1',
      bgColor: '#eef2ff',
      onClick: () => handleCardClick({})
    },
    {
      title: 'Active Leads',
      value: summary?.active_leads || 0,
      icon: UserCheck,
      color: '#f59e0b',
      bgColor: '#fffbeb',
      onClick: () => handleCardClick({ status: 'New,In Process' })
    },
    {
      title: 'Booked/Converted',
      value: summary?.booked_leads || 0,
      icon: TrendingUp,
      color: '#10b981',
      bgColor: '#d1fae5',
      onClick: () => handleCardClick({ status: 'Booked,Converted' })
    },
    {
      title: 'Upcoming Travels',
      value: summary?.upcoming_travels || 0,
      icon: Calendar,
      color: '#8b5cf6',
      bgColor: '#f3e8ff',
      onClick: () => navigate('/crm/upcoming')
    },
    {
      title: "Today's Reminders",
      value: summary?.today_reminders || 0,
      icon: Bell,
      color: '#ef4444',
      bgColor: '#fee2e2',
      onClick: () => navigate('/crm/reminders')
    },
    {
      title: 'Total Referrals',
      value: summary?.total_referrals || 0,
      icon: GitBranch,
      color: '#06b6d4',
      bgColor: '#cffafe',
      onClick: () => handleCardClick({ source: 'Referral' })
    }
  ];

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

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
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <BarChart3 size={32} style={{ color: '#6366f1' }} />
          <h1 className="page-title" style={{ margin: 0 }}>CRM Dashboard</h1>
        </div>
        <button
          onClick={() => navigate('/crm/leads?action=create')}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          Add New Lead
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div
              key={index}
              onClick={card.onClick}
              className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow duration-200"
              style={{ borderLeft: `4px solid ${card.color}` }}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="text-sm text-gray-600 font-medium">{card.title}</p>
                  <p className="text-3xl font-bold mt-2" style={{ color: card.color }}>
                    {card.value}
                  </p>
                </div>
                <div
                  style={{ backgroundColor: card.bgColor, color: card.color }}
                  className="p-3 rounded-full"
                >
                  <Icon size={24} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Monthly Leads */}
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

        {/* Lead Type Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Lead Type Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={leadTypeBreakdown}
                dataKey="count"
                nameKey="type"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {leadTypeBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Lead Source Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Lead Source Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={leadSourceBreakdown} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="source" />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#10b981" name="Leads" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default CRMDashboard;