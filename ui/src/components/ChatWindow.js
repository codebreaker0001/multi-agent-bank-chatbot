import { useEffect, useRef, useState } from "react";
import { sendMessage } from "../api";
import MessageBubble from "./MessageBubble";

// Session ID is fixed per browser tab. In a real app you'd generate one
// per login so different logins don't share history.
const SESSION_ID = `sess-${Math.random().toString(36).slice(2, 9)}`;

const WELCOME = "Hello! I'm your DemoBank assistant. I can help you with:\n• Account balance and details\n• Transaction history and spending\n• Address change, cheque book, KYC update\n\nWhat would you like help with?";

export default function ChatWindow({ token, userName, onLogout }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: WELCOME },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function addMessage(role, content) {
    setMessages((prev) => [...prev, { role, content }]);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    addMessage("user", text);
    setLoading(true);

    try {
      const data = await sendMessage(token, SESSION_ID, text);
      addMessage("assistant", data.reply);
    } catch (err) {
      addMessage("system", `⚠️ ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    // Send on Enter, new line on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <span style={styles.headerTitle}>🏦 DemoBank Assistant</span>
          <span style={styles.headerSub}> · {userName}</span>
        </div>
        <button style={styles.logoutBtn} onClick={onLogout}>
          Sign out
        </button>
      </div>

      {/* Message list */}
      <div style={styles.messageList}>
        {messages.map((msg, i) => (
          <MessageBubble key={i} role={msg.role} content={msg.content} />
        ))}

        {/* Typing indicator while waiting for a reply */}
        {loading && (
          <MessageBubble role="assistant" content="Thinking…" />
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={styles.inputBar}>
        <textarea
          style={styles.textarea}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your balance, transactions, or services…"
          rows={1}
          disabled={loading}
        />
        <button
          style={{
            ...styles.sendBtn,
            opacity: !input.trim() || loading ? 0.5 : 1,
          }}
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: "#f0f4f8",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 20px",
    background: "#fff",
    borderBottom: "1px solid #e5e7eb",
    flexShrink: 0,
  },
  headerTitle: { fontWeight: 700, fontSize: 16, color: "#1a1a2e" },
  headerSub: { fontSize: 13, color: "#6b7280" },
  logoutBtn: {
    padding: "6px 14px",
    background: "transparent",
    border: "1px solid #ddd",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 13,
    color: "#555",
  },
  messageList: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 16px",
    display: "flex",
    flexDirection: "column",
  },
  inputBar: {
    display: "flex",
    gap: 10,
    padding: "12px 16px",
    background: "#fff",
    borderTop: "1px solid #e5e7eb",
    flexShrink: 0,
  },
  textarea: {
    flex: 1,
    padding: "10px 14px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: 14,
    resize: "none",
    outline: "none",
    fontFamily: "inherit",
    lineHeight: 1.5,
  },
  sendBtn: {
    padding: "10px 20px",
    background: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    flexShrink: 0,
  },
};