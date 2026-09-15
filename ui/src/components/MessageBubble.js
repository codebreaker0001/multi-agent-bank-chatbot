/**
 * A single chat bubble.
 * role = "user"      → right-aligned, blue
 * role = "assistant" → left-aligned, white
 * role = "system"    → centred, grey (errors, status messages)
 */
export default function MessageBubble({ role, content }) {
  if (role === "system") {
    return <div style={styles.system}>{content}</div>;
  }

  const isUser = role === "user";
  return (
    <div style={{ ...styles.row, justifyContent: isUser ? "flex-end" : "flex-start" }}>
      {!isUser && <div style={styles.avatar}>🤖</div>}
      <div style={isUser ? styles.userBubble : styles.botBubble}>
        {content}
      </div>
      {isUser && <div style={styles.avatar}>👤</div>}
    </div>
  );
}

const styles = {
  row: {
    display: "flex",
    alignItems: "flex-end",
    gap: 8,
    marginBottom: 12,
  },
  avatar: { fontSize: 20, flexShrink: 0 },
  userBubble: {
    maxWidth: "70%",
    padding: "10px 14px",
    background: "#2563eb",
    color: "#fff",
    borderRadius: "16px 16px 4px 16px",
    fontSize: 14,
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
  },
  botBubble: {
    maxWidth: "70%",
    padding: "10px 14px",
    background: "#fff",
    color: "#1a1a2e",
    borderRadius: "16px 16px 16px 4px",
    fontSize: 14,
    lineHeight: 1.5,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    whiteSpace: "pre-wrap",
  },
  system: {
    textAlign: "center",
    color: "#888",
    fontSize: 12,
    margin: "8px 0",
  },
};