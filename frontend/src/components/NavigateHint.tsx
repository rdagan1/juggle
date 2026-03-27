interface NavigateHintProps {
  hint: string;
  onNavigate: (tab: string) => void;
}

const HINT_LABELS: Record<string, string> = {
  timeline: "צפה/י בלוח הזמנים",
  grades: "צפה/י בציונים",
  emails: "צפה/י במיילים",
  settings: "פתח/י הגדרות",
};

export function NavigateHint({ hint, onNavigate }: NavigateHintProps) {
  const label = HINT_LABELS[hint] ?? hint;
  return (
    <button
      onClick={() => onNavigate(hint)}
      className="mt-1 text-xs text-gio-500 underline underline-offset-2 hover:text-gio-600 text-right"
      aria-label={label}
    >
      {label} →
    </button>
  );
}
