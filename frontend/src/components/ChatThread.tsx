import { useEffect, useRef, useState } from "react";
import { type GioMessage } from "../api/client";
import { GioMessage as GioMessageComponent } from "./GioMessage";
import { UserMessage } from "./UserMessage";
import { he } from "../i18n/he";

interface ChatThreadProps {
  messages: GioMessage[];
  isLoading: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
  onButtonSelect: (messageId: string, value: string, label: string) => void;
  onNavigate: (tab: string) => void;
  // Track which messages have had buttons used
  usedMessageIds: Set<string>;
}

export function ChatThread({
  messages,
  isLoading,
  hasMore,
  onLoadMore,
  onButtonSelect,
  onNavigate,
  usedMessageIds,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, autoScroll]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    setAutoScroll(nearBottom);

    // Load more when scrolled to top
    if (el.scrollTop === 0 && hasMore) {
      onLoadMore();
    }
  };

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4"
      role="log"
      aria-live="polite"
      aria-label="שיחה עם Gio"
      dir="rtl"
    >
      {/* Load more */}
      {hasMore && (
        <button
          onClick={onLoadMore}
          className="self-center text-xs text-gray-400 hover:text-gray-600 py-2"
          aria-label={he.chat.loadMore}
        >
          {he.chat.loadMore}
        </button>
      )}

      {messages.map((msg) =>
        msg.role === "assistant" ? (
          <GioMessageComponent
            key={msg.id}
            message={msg}
            onButtonSelect={(msgId, value, label) => {
              onButtonSelect(msgId, value, label);
            }}
            onNavigate={onNavigate}
            buttonsDisabled={usedMessageIds.has(msg.id)}
          />
        ) : (
          <UserMessage key={msg.id} message={msg} />
        ),
      )}

      {/* Typing indicator */}
      {isLoading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm" aria-live="assertive" aria-label={he.chat.typing}>
          <div className="w-7 h-7 rounded-full bg-gio-500 flex items-center justify-center text-white text-xs font-bold">
            G
          </div>
          <div className="flex gap-1">
            <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce [animation-delay:300ms]" />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
