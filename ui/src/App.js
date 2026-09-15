/**
 * App.js — top-level state: are we logged in or not?
 *
 * auth state:
 *   null                → show Login screen
 *   { token, name }     → show ChatWindow
 *
 * The JWT is kept in React state (memory), not localStorage.
 * Why? localStorage is accessible to any JS on the page (XSS risk).
 * In-memory means the token is gone when the tab closes, which is fine
 * for a banking session.
 */

import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import Login from "./components/Login";

export default function App() {
  const [auth, setAuth] = useState(null);

  function handleLogin(data) {
    // data = { access_token, customer_id, name }
    setAuth({ token: data.access_token, name: data.name });
  }

  function handleLogout() {
    setAuth(null);
  }

  if (!auth) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <ChatWindow
      token={auth.token}
      userName={auth.name}
      onLogout={handleLogout}
    />
  );
}