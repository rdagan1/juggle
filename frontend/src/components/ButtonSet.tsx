import { useState } from "react";
import { type GioButton } from "../api/client";
import { he } from "../i18n/he";

interface ButtonSetProps {
  buttons: GioButton[];
  messageId: string;
  onSelect: (messageId: string, value: string, label: string) => void;
  disabled?: boolean;
}

export function ButtonSet({ buttons, messageId, onSelect, disabled = false }: ButtonSetProps) {
  const [showEscapeHatch, setShowEscapeHatch] = useState(false);
  const [freeText, setFreeText] = useState("");

  const handleButtonClick = (btn: GioButton) => {
    if (disabled) return;
    onSelect(messageId, btn.value, btn.label);
  };

  const handleFreeTextSubmit = () => {
    if (!freeText.trim() || disabled) return;
    onSelect(messageId, freeText.trim(), freeText.trim());
    setFreeText("");
    setShowEscapeHatch(false);
  };

  return (
    <div className="mt-2 flex flex-col gap-2" dir="rtl">
      {/* Pill buttons — max 4 per row, wrap */}
      <div className="flex flex-wrap gap-2 justify-start">
        {buttons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => handleButtonClick(btn)}
            disabled={disabled}
            className="min-h-[44px] px-4 py-2 rounded-full border border-gio-500 text-gio-600 text-sm font-medium
                       hover:bg-gio-50 active:bg-gio-100 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
            aria-label={btn.label}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Escape hatch accordion */}
      <div>
        <button
          onClick={() => setShowEscapeHatch((v) => !v)}
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          aria-expanded={showEscapeHatch}
        >
          {he.chat.otherOption}
        </button>
        {showEscapeHatch && (
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleFreeTextSubmit()}
              placeholder={he.chat.inputPlaceholder}
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-gio-500"
              dir="rtl"
              aria-label="הקלד/י הודעה חופשית"
            />
            <button
              onClick={handleFreeTextSubmit}
              disabled={!freeText.trim()}
              className="min-h-[44px] px-4 rounded-lg bg-gio-500 text-white text-sm font-medium
                         hover:bg-gio-600 disabled:opacity-40 transition-colors"
              aria-label={he.chat.sendButton}
            >
              {he.chat.sendButton}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
