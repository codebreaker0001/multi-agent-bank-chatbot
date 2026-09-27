import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowDown } from "lucide-react";
import { refreshAccessToken, sendMessage } from "../../api";
import { inferContext } from "../../utils/inferContext";
import { suggestionCards } from "../../services/mockBankingData";
import ChatMessage, { SecureNotice } from "./ChatMessage";
import ChatInput from "./ChatInput";
import ToolExecution from "./ToolExecution";
import { WelcomeSuggestions } from "./SuggestionCards";

// One session per browser tab. In a real app you'd generate one per login
// so different logins don't share history.
const SESSION_ID = `sess-${Math.random().toString(36).slice(2, 9)}`;

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ChatWindow({ token, refreshToken, userName, onTokenRefresh, onLogout, onContextHint }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const bottomRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function addMessage(role, content, agent) {
    setMessages((prev) => [...prev, { role, content, agent, timestamp: timeNow() }]);
  }

  function handleScroll() {
    const el = listRef.current;
    if (!el) return;
    setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 200);
  }

  // The access token expires in 15 min. On a 401, use the refresh token to
  // get a new one and retry once before giving up.
  async function sendWithRefresh(text) {
    try {
      return await sendMessage(token, SESSION_ID, text);
    } catch (err) {
      if (err.status !== 401 || !refreshToken) throw err;
      try {
        const { access_token } = await refreshAccessToken(refreshToken);
        onTokenRefresh(access_token);
        return await sendMessage(access_token, SESSION_ID, text);
      } catch {
        onLogout();
        throw new Error("Session expired. Please log in again.");
      }
    }
  }

  async function handleSend(overrideText) {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;

    setInput("");
    addMessage("user", text);
    onContextHint?.(inferContext(text));
    setLoading(true);

    try {
      const data = await sendWithRefresh(text);
      addMessage("assistant", data.reply, data.agent);
    } catch (err) {
      addMessage("system", err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleRegenerate() {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser) return;
    setMessages((prev) => prev.slice(0, -1)); // drop the last assistant reply
    handleSend(lastUser.content);
  }

  const lastAssistantIndex = messages.map((m) => m.role).lastIndexOf("assistant");

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      <div ref={listRef} onScroll={handleScroll} className="relative flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-6 px-4 text-center">
            <div>
              <h1 className="text-2xl font-bold text-navy-900">Good {timeOfDay()}, {userName?.split(" ")[0] || "there"} 👋</h1>
              <p className="mt-1 text-sm text-navy-400">What would you like to do today?</p>
            </div>
            <WelcomeSuggestions cards={suggestionCards} onSelect={(prompt) => handleSend(prompt)} />
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col px-4 py-5">
            <div className="mb-3 flex justify-center">
              <SecureNotice />
            </div>
            <AnimatePresence initial={false}>
              {messages.map((m, i) => (
                <ChatMessage
                  key={i}
                  role={m.role}
                  content={m.content}
                  agent={m.agent}
                  timestamp={m.timestamp}
                  isLast={i === lastAssistantIndex}
                  onRegenerate={handleRegenerate}
                />
              ))}
            </AnimatePresence>

            {loading && (
              <motion.div
                className="flex items-center gap-2 py-2 pl-9"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <ToolExecution />
              </motion.div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {showScrollBtn && (
          <button
            onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })}
            className="absolute bottom-4 left-1/2 flex h-8 w-8 -translate-x-1/2 items-center justify-center rounded-full border border-navy-100 bg-white text-navy-500 shadow-card hover:bg-navy-50"
            aria-label="Scroll to latest message"
          >
            <ArrowDown size={15} />
          </button>
        )}
      </div>

      <ChatInput value={input} onChange={setInput} onSend={() => handleSend()} disabled={loading} />
    </div>
  );
}

function timeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}
