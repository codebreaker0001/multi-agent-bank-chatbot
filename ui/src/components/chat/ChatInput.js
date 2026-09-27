import { useState } from "react";
import { ArrowUp } from "lucide-react";
import { InputChips } from "./SuggestionCards";
import { inputSuggestions } from "../../services/mockBankingData";

export default function ChatInput({ value, onChange, onSend, disabled }) {
  const [focused, setFocused] = useState(false);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-4 pb-4">
      <div className="mb-2">
        <InputChips items={inputSuggestions} onSelect={(text) => onChange(text)} />
      </div>

      <div
        className={`flex items-end gap-2 rounded-2xl border bg-white p-2 pl-4 shadow-card transition-all duration-150 ${
          focused ? "border-accent-500 shadow-[0_0_0_3px_rgba(59,91,219,0.12)]" : "border-navy-100"
        }`}
      >
        <textarea
          className="max-h-32 flex-1 resize-none border-none bg-transparent py-2 text-sm text-navy-800 placeholder:text-navy-300 focus:outline-none"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Ask anything about your finances…"
          rows={1}
          disabled={disabled}
        />
        <button
          onClick={onSend}
          disabled={!value.trim() || disabled}
          aria-label="Send message"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-navy-900 text-white
            transition-all duration-150 hover:bg-navy-800 disabled:bg-navy-100 disabled:text-navy-300"
        >
          <ArrowUp size={16} />
        </button>
      </div>
      <div className="mt-1.5 px-1 text-[11px] text-navy-300">Enter to send · Shift + Enter for a new line</div>
    </div>
  );
}
