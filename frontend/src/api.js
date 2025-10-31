// src/api.js

// ✅ Render backend URL (replace with your backend’s Render URL)
const API_BASE_URL = process.env.REACT_APP_API_URL || "https://backend-mwh2.onrender.com";

// ================== LEADS ==================

export async function getLeads() {
  const response = await fetch(`${API_BASE_URL}/crm/leads`);
  if (!response.ok) throw new Error("Failed to fetch leads");
  return response.json();
}

export async function createLead(data) {
  const response = await fetch(`${API_BASE_URL}/crm/leads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create lead");
  return response.json();
}

export async function deleteLead(id) {
  const response = await fetch(`${API_BASE_URL}/crm/leads/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete lead");
  return response.json();
}

// ================== DASHBOARD ==================

export async function getDashboardSummary() {
  const response = await fetch(`${API_BASE_URL}/crm/dashboard-summary`);
  if (!response.ok) throw new Error("Failed to fetch dashboard summary");
  return response.json();
}

// ================== REMINDERS ==================

export async function getReminders() {
  const response = await fetch(`${API_BASE_URL}/crm/reminders`);
  if (!response.ok) throw new Error("Failed to fetch reminders");
  return response.json();
}

export async function createReminder(data) {
  const response = await fetch(`${API_BASE_URL}/crm/reminders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create reminder");
  return response.json();
}
