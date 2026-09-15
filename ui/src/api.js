/**
 * api.js — all calls to the backend in one place.
 *
 * Reads REACT_APP_API_URL from .env so you can point at localhost
 * during dev and a real server in production without changing code.
 */

const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

function authHeaders(token) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function login(customerId, password) {
  const res = await fetch(`${BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_id: customerId, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json(); // { access_token, customer_id, name }
}

export async function sendMessage(token, sessionId, message) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || err.detail || "Something went wrong");
  }
  return res.json(); // { reply, session_id }
}

export async function serviceAction(token, payload) {
  const res = await fetch(`${BASE}/service/action`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Action failed");
  }
  return res.json(); // { message }
}