import { useState } from "react";
import { type GioMessage } from "../api/client";

interface UserMessageProps {
  message: GioMessage;
}

const TYPE_ICONS: Record<string, string> = {
  deadline: "📅",
  grade: "📊",
  course: "📚",
  pdf: "📄",
};

export function UserMessage({ message }: UserMessageProps) {
  const [showAttachments, setShowAttachments] = useState(false);
  const attachments = message._attachments;

  return (
    <div className="flex flex-col items-start max-w-[75%] self-start" dir="rtl">
      <div className="relative">
        <div className="bg-gio-500 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>

        {/* Attachment indicator button */}
        {attachments && attachments.length > 0 && (
          <div className="absolute -bottom-2 left-1">
            <button
              type="button"
              onClick={() => setShowAttachments((v) => !v)}
              className="flex items-center gap-0.5 bg-white border border-gio-100 rounded-full px-1.5 py-0.5 text-[10px] text-gio-600 shadow-sm hover:bg-gio-50 transition-colors"
              aria-label="הצג קבצים מצורפים"
              aria-expanded={showAttachments}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
              <span>{attachments.length}</span>
            </button>
          </div>
        )}
      </div>

      {/* Attachment dropdown */}
      {showAttachments && attachments && attachments.length > 0 && (
        <div
          className="mt-3 bg-white border border-navy-100 rounded-xl shadow-md py-1 min-w-[160px] max-w-[220px]"
          dir="rtl"
          role="list"
          aria-label="פריטים מצורפים"
        >
          {attachments.map((a) => (
            <div
              key={a.id}
              className="flex items-center gap-2 px-3 py-2 text-xs text-gray-700"
              role="listitem"
            >
              <span aria-hidden="true">{TYPE_ICONS[a.type] ?? "📎"}</span>
              <div className="flex flex-col min-w-0">
                <span className="font-medium truncate">{a.title}</span>
                {a.subtitle && (
                  <span className="text-slate-400 truncate">{a.subtitle}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <time
        className="mt-1 text-[10px] text-navy-200"
        dateTime={message.timestamp}
      >
        {new Date(message.timestamp).toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" })}
      </time>
    </div>
  );
}
