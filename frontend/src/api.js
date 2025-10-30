// src/api.js

const API_BASE_URL = process.env.REACT_APP_API_URL || "https://unified-super-app-5.onrender.com"; 

// Example function to fetch clients
export async function getClients() {
  const response = await fetch(`${API_BASE_URL}/api/clients`);
  if (!response.ok) throw new Error("Failed to fetch clients");
  return response.json();
}

// Example function to create a new booking
export async function createBooking(data) {
  const response = await fetch(`${API_BASE_URL}/api/bookings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create booking");
  return response.json();
}
