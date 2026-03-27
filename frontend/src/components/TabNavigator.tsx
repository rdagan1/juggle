import { he } from "../i18n/he";

export type TabId = "gio" | "timeline" | "grades" | "courses" | "emails" | "settings";

interface TabNavigatorProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  badges?: Partial<Record<TabId, number>>;
}

function IconChat() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M2 3h16v11H6.5L2 18V3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

function IconCalendar() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="2" y="3" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M6 1v4M14 1v4M2 8h16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function IconChart() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <rect x="2" y="12" width="4" height="6" rx="1" />
      <rect x="8" y="8" width="4" height="10" rx="1" />
      <rect x="14" y="4" width="4" height="14" rx="1" />
    </svg>
  );
}

function IconEnvelope() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="2" y="4" width="16" height="13" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M2 7l8 5 8-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function IconBook() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M4 3h9a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M7 7h5M7 10h5M7 13h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function IconSliders() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="5" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="13" cy="10" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="7" cy="15" r="2" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

const TAB_ICONS: Record<TabId, React.ReactNode> = {
  gio: <IconChat />,
  timeline: <IconCalendar />,
  grades: <IconChart />,
  courses: <IconBook />,
  emails: <IconEnvelope />,
  settings: <IconSliders />,
};

const TABS: { id: TabId; label: string }[] = [
  { id: "gio", label: he.tabs.gio },
  { id: "timeline", label: he.tabs.timeline },
  { id: "grades", label: he.tabs.grades },
  { id: "courses", label: he.tabs.courses },
  { id: "emails", label: he.tabs.emails },
  { id: "settings", label: he.tabs.settings },
];

export function TabNavigator({ activeTab, onTabChange, badges = {} }: TabNavigatorProps) {
  return (
    <nav
      className="flex bg-[#0f2040] safe-area-inset-bottom"
      role="tablist"
      aria-label="ניווט ראשי"
      dir="rtl"
    >
      {TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        const badge = badges[tab.id];
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            className={`flex-1 flex flex-col items-center justify-center py-3 gap-1 relative
                        min-h-[56px] transition-colors
                        ${isActive ? "text-gio-500" : "text-white/60 hover:text-white/80"}`}
            aria-label={tab.label}
          >
            {TAB_ICONS[tab.id]}
            <span className="text-[10px] font-medium">{tab.label}</span>
            {badge != null && badge > 0 && (
              <span
                className="absolute top-2 right-[calc(50%-16px)] w-4 h-4 rounded-full bg-urgent text-white text-[9px] flex items-center justify-center font-bold"
                aria-label={`${badge} פריטים חדשים`}
              >
                {badge > 9 ? "9+" : badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
