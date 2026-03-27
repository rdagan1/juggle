import { useRef, useState } from "react";
import { ChatThread } from "../components/ChatThread";
import { FileDropzone, UploadButton } from "../components/FileDropzone";
import { useGioChat } from "../hooks/useGioChat";
import { he } from "../i18n/he";
import { type TabId } from "../components/TabNavigator";
import { type GioAttachment, type AttachmentRef } from "../api/client";

interface GioTabProps {
  userId: string;
  onNavigate: (tab: TabId) => void;
  attachments?: GioAttachment[];
  onAddAttachment?: (attachment: GioAttachment) => void;
  onRemoveAttachment?: (id: string) => void;
}

export function GioTab({ userId, onNavigate, attachments = [], onAddAttachment, onRemoveAttachment }: GioTabProps) {
  const { messages, isLoading, hasMore, loadMore, sendResponse, dismissButtons } = useGioChat(userId);
  const [input, setInput] = useState("");
  const [usedMessageIds, setUsedMessageIds] = useState<Set<string>>(new Set());
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resizeTextarea = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
  };

  const handleButtonSelect = async (messageId: string, value: string, label: string) => {
    setUsedMessageIds((prev) => new Set([...prev, messageId]));
    dismissButtons(messageId);
    await sendResponse(messageId, value, undefined, label);
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    const attachmentRefs: AttachmentRef[] | undefined = attachments.length > 0
      ? attachments.map((a) => ({ type: a.type, id: a.id }))
      : undefined;
    const attachmentDisplay = attachments.length > 0 ? [...attachments] : undefined;
    attachments.forEach((a) => onRemoveAttachment?.(a.id));
    await sendResponse(null, undefined, text, undefined, attachmentRefs, attachmentDisplay);
  };

  return (
    <div
      id="panel-gio"
      role="tabpanel"
      aria-label={he.tabs.gio}
      className="flex flex-col h-full bg-navy-50"
      dir="rtl"
    >
      {/* Global PDF drag-drop overlay */}
      <FileDropzone onAttachment={onAddAttachment} />

      {/* Message thread */}
      <ChatThread
        messages={messages}
        isLoading={isLoading}
        hasMore={hasMore}
        onLoadMore={loadMore}
        onButtonSelect={handleButtonSelect}
        onNavigate={onNavigate}
        usedMessageIds={usedMessageIds}
      />

      {/* Input area */}
      <form
        onSubmit={handleTextSubmit}
        className="border-t border-navy-100 bg-white px-4 py-3 flex flex-col gap-2"
        aria-label="שליחת הודעה"
      >
        {/* Attachment chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5" dir="rtl" aria-label="פריטים מצורפים">
            {attachments.map((a) => (
              <div
                key={a.id}
                className="flex items-center gap-1 bg-gio-50 border border-gio-100 rounded-lg px-2 py-1 text-xs text-gio-700 max-w-[200px]"
              >
                <span className="truncate">{a.title}</span>
                {a.subtitle && (
                  <span className="text-gio-400 shrink-0 truncate max-w-[80px]">· {a.subtitle}</span>
                )}
                <button
                  type="button"
                  onClick={() => onRemoveAttachment?.(a.id)}
                  className="shrink-0 text-gio-400 hover:text-gio-700 ml-0.5"
                  aria-label={`הסר ${a.title}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="flex gap-2 items-end">
          <UploadButton onAttachment={onAddAttachment} />
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); resizeTextarea(); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleTextSubmit(e as unknown as React.FormEvent);
              }
            }}
            placeholder={he.chat.inputPlaceholder}
            rows={1}
            className="flex-1 resize-none rounded-xl border border-navy-200 px-4 py-3 text-sm focus:outline-none focus:border-gio-500
                       min-h-[44px] max-h-32 overflow-hidden"
            dir="rtl"
            aria-label={he.chat.inputPlaceholder}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="min-h-[44px] min-w-[44px] rounded-xl bg-gio-500 text-white flex items-center justify-center
                       hover:bg-gio-600 disabled:opacity-40 transition-colors"
            aria-label={he.chat.sendButton}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
