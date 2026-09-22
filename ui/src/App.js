/**
 * App.js — top-level state: are we logged in or not?
 *
 * auth state:
 *   null                                  → show Login screen
 *   { token, refreshToken, name }         → show ChatWindow
 *
 * Both JWTs are kept in React state (memory), not localStorage.
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
    // data = { access_token, refresh_token, customer_id, name }
    setAuth({ token: data.access_token, refreshToken: data.refresh_token, name: data.name });
  }

  function handleLogout() {
    setAuth(null);
  }

  function handleTokenRefresh(accessToken) {
    setAuth((prev) => ({ ...prev, token: accessToken }));
  }

  if (!auth) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <ChatWindow
      token={auth.token}
      refreshToken={auth.refreshToken}
      userName={auth.name}
      onLogout={handleLogout}
      onTokenRefresh={handleTokenRefresh}
    />
  );
}