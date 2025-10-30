import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { DollarSign, TrendingUp, TrendingDown, Users, Calendar, Bell, RefreshCw, Clock } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL || '';

function Dashboard() {
  const navigate = useNavigate();
  const role = localStorage.getItem('role');
  const [summary, setSummary] = useState(null);
  const [monthlyData, setMonthlyData] = useState([]);
  const [expenseBreakdown, setExpenseBreakdown] = useState([]);
  const [profitTrend, setProfitTrend] = useState([]);
  const [upcomingTravels, setUpcomingTravels] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [crmSummary, setCrmSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const year = new Date().getFullYear();
      const [summaryRes, monthlyRes, expenseRes, profitRes, crmRes, travelRes, reminderRes] = await Promise.all([
        axios.get(`${API}/api/dashboard/summary`),
        axios.get(`${API}/api/dashboard/monthly?year=${year}`),
        axios.get(`${API}/api/reports?type=expense-breakdown`),
        axios.get(`${API}/api/reports?type=profit-loss-trend&year=${year}`),
        axios.get(`${API}/api/crm/dashboard-summary`),
        axios.get(`${API}/api/crm/upcoming-travels-dashboard`),
        axios.get(`${API}/api/crm/reminders?status=Pending`)
      ]);

      setSummary(summaryRes.data);
      setMonthlyData(monthlyRes.data);
      setExpenseBreakdown(expenseRes.data.breakdown || []);
      setProfitTrend(profitRes.data.trend || []);
      setCrmSummary(crmRes.data);
      setUpcomingTravels(travelRes.data || []);
      setReminders(reminderRes.data.slice(0, 5) || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      const response = await axios.get(`${API}/api/sync/crm-finance`);
      toast.success(`Synced: ${response.data.synced} new entries, ${response.data.skipped} already synced`);
      fetchDashboardData();
    } catch (error) {
      console.error('Sync error:', error);
      toast.error('Failed to sync CRM & Finance');
    } finally {
      setSyncing(false);
    }
  };

  const cards = [
    {
      title: 'Total Revenue',
      value: `₹${summary?.total_revenue?.toLocaleString() || 0}`,
      icon: DollarSign,
      color: '#10b981',
      bgColor: '#d1fae5',
      onClick: () => navigate('/revenue')
    },
    {
      title: 'Total Expenses',
      value: `₹${summary?.total_expenses?.toLocaleString() || 0}`,
      icon: TrendingDown,
      color: '#ef4444',
      bgColor: '#fee2e2',
      onClick: () => navigate('/expenses')
    },
    {
      title: 'Net Profit',
      value: `₹${summary?.net_profit?.toLocaleString() || 0}`,
      icon: TrendingUp,
      color: '#6366f1',
      bgColor: '#eef2ff',
      onClick: () => navigate('/reports')
    },
    {
      title: 'Pending Payments',
      value: `₹${summary?.pending_amount?.toLocaleString() || 0}`,
      icon: Clock,
      color: '#f59e0b',
      bgColor: '#fef3c7',
      onClick: () => navigate('/pending')
    }
  ];

  const crmCards = [
    {
      title: 'Active Leads',
      value: crmSummary?.active_leads || 0,
      icon: Users,
      color: '#8b5cf6',
      bgColor: '#f3e8ff',
      onClick: () => navigate('/crm/leads', { state: { status: 'New,In Process' } })
    },
    {
      title: 'Booked Leads',
      value: crmSummary?.booked_leads || 0,
      icon: Calendar,
      color: '#10b981',
      bgColor: '#d1fae5',
      onClick: () => navigate('/crm/leads', { state: { status: 'Booked,Converted' } })
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
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title">Business Dashboard</h1>
        {role === 'admin' && (
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn btn-primary flex items-center gap-2"
          >
            <RefreshCw size={18} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing...' : 'Sync CRM & Finance'}
          </button>
        )}
      </div>

      {/* Finance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div
              key={index}
              onClick={card.onClick}
              className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow"
              style={{ borderLeft: `4px solid ${card.color}` }}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-gray-600 font-medium">{card.title}</p>
                  <p className="text-2xl font-bold mt-2" style={{ color: card.color }}>
                    {card.value}
                  </p>
                </div>
                <div style={{ backgroundColor: card.bgColor, color: card.color }} className="p-3 rounded-full">
                  <Icon size={24} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* CRM Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {crmCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div
              key={index}
              onClick={card.onClick}
              className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow"
              style={{ borderLeft: `4px solid ${card.color}` }}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-gray-600 font-medium">{card.title}</p>
                  <p className="text-3xl font-bold mt-2" style={{ color: card.color }}>
                    {card.value}
                  </p>
                </div>
                <div style={{ backgroundColor: card.bgColor, color: card.color }} className="p-3 rounded-full">
                  <Icon size={24} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue vs Expenses</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="revenue" fill="#10b981" name="Revenue" />
              <Bar dataKey="expenses" fill="#ef4444" name="Expenses" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Expense Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={expenseBreakdown} dataKey="amount" nameKey="category" cx="50%" cy="50%" outerRadius={100} label>
                {expenseBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Upcoming Travel & Reminders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Calendar size={20} />
              Upcoming Travel (Next 30 Days)
            </h3>
            <button onClick={() => navigate('/crm/upcoming')} className="text-sm text-indigo-600 hover:text-indigo-800">
              View All
            </button>
          </div>
          {upcomingTravels.length > 0 ? (
            <div className="space-y-2">
              {upcomingTravels.slice(0, 5).map((travel) => (
                <div key={travel._id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium text-sm">{travel.client_name}</p>
                    <p className="text-xs text-gray-500">{travel.lead_type}</p>
                  </div>
                  <p className="text-sm font-medium text-indigo-600">
                    {new Date(travel.travel_date).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No upcoming travel</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Bell size={20} />
              Recent Reminders
            </h3>
            <button onClick={() => navigate('/crm/reminders')} className="text-sm text-indigo-600 hover:text-indigo-800">
              View All
            </button>
          </div>
          {reminders.length > 0 ? (
            <div className="space-y-2">
              {reminders.map((reminder) => (
                <div key={reminder._id} className="flex justify-between items-start p-2 bg-gray-50 rounded">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{reminder.title}</p>
                    <p className="text-xs text-gray-500">{new Date(reminder.date).toLocaleString()}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    reminder.priority === 'High' ? 'bg-red-100 text-red-800' :
                    reminder.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {reminder.priority}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No pending reminders</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
