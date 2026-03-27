import ReactMarkdown from "react-markdown";
import { type GioMessage as GioMsg } from "../api/client";
import { ButtonSet } from "./ButtonSet";
import { NavigateHint } from "./NavigateHint";

interface GioMessageProps {
  message: GioMsg;
  onButtonSelect: (messageId: string, value: string, label: string) => void;
  onNavigate: (tab: string) => void;
  buttonsDisabled?: boolean;
}

export function GioMessage({ message, onButtonSelect, onNavigate, buttonsDisabled }: GioMessageProps) {
  const hasButtons = message.buttons && message.buttons.length > 0;

  return (
    <div className="flex flex-col items-end max-w-[85%] self-end" dir="rtl">
      {/* Avatar + bubble — avatar on the left (last in RTL row) */}
      <div className="flex items-end gap-2">
        <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 text-sm text-gray-800 leading-relaxed gio-prose">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        <div
          className="w-7 h-7 rounded-full bg-gio-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
          aria-hidden="true"
        >
          G
        </div>
      </div>

      {/* Buttons */}
      {hasButtons && (
        <div className="ml-9 mt-1 w-full">
          <ButtonSet
            buttons={message.buttons!}
            messageId={message.id}
            onSelect={onButtonSelect}
            disabled={buttonsDisabled}
          />
        </div>
      )}

      {/* Navigate hint */}
      {message.navigate_hint && (
        <div className="ml-9 mt-1">
          <NavigateHint hint={message.navigate_hint} onNavigate={onNavigate} />
        </div>
      )}

      {/* Timestamp */}
      <time
        className="ml-9 mt-1 text-[10px] text-navy-200"
        dateTime={message.timestamp}
        aria-label={new Date(message.timestamp).toLocaleTimeString("he-IL")}
      >
        {new Date(message.timestamp).toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" })}
      </time>
    </div>
  );
}
