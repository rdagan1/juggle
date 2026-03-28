import { useEffect, useState } from "react";
import { timelineApi, type DeadlineItem, type GioAttachment } from "../api/client";
import { he, SOURCE_LABELS } from "../i18n/he";
import { type TabId } from "../components/TabNavigator";
import { CalendarView } from "../components/CalendarView";
import { ThreeDotMenu } from "../components/ThreeDotMenu";

interface TimelineTabProps {
  onNavigate: (tab: TabId) => void;
  filterCourseId?: string;
  onFilterCourseName?: (name: string) => void;
  onAskGio?: (attachment: GioAttachment) => void;
}

type ViewMode = "list" | "calendar";

function deadlineToAttachment(item: DeadlineItem): GioAttachment {
  return {
    id: item.id,
    type: "deadline",
    title: item.title,
    subtitle: item.course_name,
  };
}

function ViewToggle({ view, onChange }: { view: ViewMode; onChange: (v: ViewMode) => void }) {
  return (
    <div className="flex gap-1 bg-navy-100 rounded-full p-0.5" role="group" aria-label="בחירת תצוגה" dir="rtl">
      {(["list", "calendar"] as ViewMode[]).map((mode) => (
        <button
          key={mode}
          onClick={() => onChange(mode)}
          className={`flex-1 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
            view === mode ? "bg-gio-500 text-white shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
          aria-pressed={view === mode}
        >
          {mode === "calendar" ? he.timeline.viewCalendar : he.timeline.viewList}
        </button>
      ))}
    </div>
  );
}

function DeadlineCard({
  item,
  onGioAction,
  onDelete,
}: {
  item: DeadlineItem;
  onGioAction: () => void;
  onDelete: (id: string) => void;
}) {
  const due = new Date(item.due_date);
  const dueFmt = due.toLocaleDateString("he-IL", { day: "numeric", month: "numeric", year: "2-digit" });
  const timeFmt = due.toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" });

  const typeLabel = he.timeline.types[item.type as keyof typeof he.timeline.types] ?? item.type;
  const statusLabel = he.timeline.statuses[item.status as keyof typeof he.timeline.statuses] ?? item.status;

  const typeColors: Record<string, string> = {
    assignment: "bg-blue-100 text-blue-700",
    exam: "bg-red-100 text-red-700",
    lecture: "bg-green-100 text-green-700",
    announcement: "bg-gray-100 text-gray-600",
  };
  const badgeColor = typeColors[item.type] ?? "bg-gray-100 text-gray-600";

  return (
    <div
      className={`bg-white rounded-xl border px-4 py-3 flex flex-col gap-1 ${
        item.is_urgent ? "border-urgent shadow-sm shadow-red-100" : "border-navy-100"
      }`}
      dir="rtl"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5 flex-1 min-w-0">
          <p className="font-medium text-sm text-gray-800 truncate">{item.title}</p>
          <p className="text-xs font-medium text-slate-600">{item.course_name}</p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${badgeColor}`}>
            {typeLabel}
          </span>
          {item.moed && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-purple-100 text-purple-700">
              מועד {item.moed}
            </span>
          )}
          <ThreeDotMenu
            items={[
              {
                label: he.menu.delete,
                onClick: () => onDelete(item.id),
                danger: true,
              },
            ]}
          />
        </div>
      </div>

      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{dueFmt} {timeFmt}</span>
          <span className="text-slate-300">·</span>
          <span className="text-slate-400">{SOURCE_LABELS[item.source] ?? item.source}</span>
          {item.needs_review && (
            <span className="text-amber-600 font-medium">{he.timeline.needsReview}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {item.estimated_hours != null && (
            <span className="text-[10px] text-slate-400">
              ~{item.estimated_hours.toFixed(1)}ש׳
            </span>
          )}
          {item.status !== "pending" && (
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
              item.status === "completed" ? "bg-green-100 text-green-700" :
              "bg-red-100 text-red-700"
            }`}>
              {statusLabel}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={onGioAction}
        className="self-end text-[10px] text-gio-500 hover:underline mt-1 min-h-[32px] px-2"
        aria-label={`פתח/י שיחה עם Gio על ${item.title}`}
      >
        שאל/י את Gio
      </button>
    </div>
  );
}

export function TimelineTab({ onNavigate, filterCourseId, onFilterCourseName, onAskGio }: TimelineTabProps) {
  const [items, setItems] = useState<DeadlineItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("list");

  useEffect(() => {
    setIsLoading(true);
    timelineApi
      .get(30, filterCourseId)
      .then(({ data }) => {
        setItems(data.items);
        if (filterCourseId && data.items.length > 0 && onFilterCourseName) {
          onFilterCourseName(data.items[0].course_name);
        }
      })
      .catch(() => setError(he.errors.generic))
      .finally(() => setIsLoading(false));
  }, [filterCourseId]);

  const handleDelete = (id: string) => {
    timelineApi
      .delete(id)
      .then(() => setItems((prev) => prev.filter((i) => i.id !== id)))
      .catch(() => setError(he.errors.generic));
  };

  const urgent = items.filter((i) => i.is_urgent);
  const rest = items.filter((i) => !i.is_urgent);

  return (
    <div
      id="panel-timeline"
      role="tabpanel"
      aria-label={he.tabs.timeline}
      className="flex flex-col h-full bg-navy-50 overflow-y-auto"
      dir="rtl"
    >
      <header className="px-4 pt-5 pb-3 flex flex-col gap-3">
        <h1 className="text-xl font-bold text-gray-800">{he.timeline.title}</h1>
        <ViewToggle view={view} onChange={setView} />
      </header>

      {isLoading && (
        <div className="flex-1 flex items-center justify-center text-slate-400">טוען...</div>
      )}

      {error && (
        <div className="mx-4 p-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>
      )}

      {!isLoading && !error && view === "calendar" && (
        <CalendarView items={items} />
      )}

      {!isLoading && !error && view === "list" && (
        <>
          {items.length === 0 && (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
              {he.timeline.noDeadlines}
            </div>
          )}

          {urgent.length > 0 && (
            <section className="px-4 mb-4" aria-label={he.timeline.urgentStrip}>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-urgent animate-pulse" aria-hidden="true" />
                <h2 className="text-xs font-semibold text-urgent uppercase tracking-wide">
                  {he.timeline.urgentStrip}
                </h2>
              </div>
              <div className="flex flex-col gap-2">
                {urgent.map((item) => (
                  <DeadlineCard
                    key={item.id}
                    item={item}
                    onGioAction={() => { onAskGio?.(deadlineToAttachment(item)); onNavigate("gio"); }}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            </section>
          )}

          {rest.length > 0 && (
            <section className="px-4 pb-6" aria-label="מטלות קרובות">
              <div className="flex flex-col gap-2">
                {rest.map((item) => (
                  <DeadlineCard
                    key={item.id}
                    item={item}
                    onGioAction={() => { onAskGio?.(deadlineToAttachment(item)); onNavigate("gio"); }}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
