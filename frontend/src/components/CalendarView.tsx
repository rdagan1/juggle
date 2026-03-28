import { useState } from "react";
import { type DeadlineItem } from "../api/client";
import { he, SOURCE_LABELS } from "../i18n/he";

interface CalendarViewProps {
  items: DeadlineItem[];
}

type ViewYear = number;
type ViewMonth = number; // 0-indexed

interface MonthYear {
  year: ViewYear;
  month: ViewMonth;
}

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function dotColorForType(type: string): string {
  if (type === "exam") return "bg-purple-500";
  if (type === "assignment") return "bg-gio-500";
  return "bg-slate-400";
}

function buildCalendarGrid(year: ViewYear, month: ViewMonth): (Date | null)[] {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDow = firstDay.getDay(); // 0=Sun
  const totalDays = lastDay.getDate();
  const cells: (Date | null)[] = [];

  for (let i = 0; i < startDow; i++) {
    cells.push(null);
  }
  for (let d = 1; d <= totalDays; d++) {
    cells.push(new Date(year, month, d));
  }
  const remainder = cells.length % 7;
  if (remainder !== 0) {
    for (let i = 0; i < 7 - remainder; i++) {
      cells.push(null);
    }
  }
  return cells;
}

function deadlinesForDay(items: DeadlineItem[], day: Date): DeadlineItem[] {
  return items.filter((item) => {
    const due = new Date(item.due_date);
    return isSameDay(due, day);
  });
}

function MonthHeader({ current, onPrev, onNext }: { current: MonthYear; onPrev: () => void; onNext: () => void }) {
  const label = new Date(current.year, current.month, 1).toLocaleDateString("he-IL", {
    month: "long",
    year: "numeric",
  });
  return (
    <div className="flex items-center justify-between px-1 mb-3">
      <button
        onClick={onPrev}
        className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-navy-100 text-gray-600 text-lg"
        aria-label="חודש קודם"
      >
        ‹
      </button>
      <span className="text-sm font-semibold text-gray-800">{label}</span>
      <button
        onClick={onNext}
        className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-navy-100 text-gray-600 text-lg"
        aria-label="חודש הבא"
      >
        ›
      </button>
    </div>
  );
}

function DayCell({
  day,
  dots,
  isSelected,
  isToday,
  onSelect,
}: {
  day: Date | null;
  dots: string[];
  isSelected: boolean;
  isToday: boolean;
  onSelect: () => void;
}) {
  if (day === null) {
    return <div className="h-10" />;
  }
  return (
    <button
      onClick={onSelect}
      className={`h-10 w-full flex flex-col items-center justify-center rounded-lg text-xs font-medium transition-colors ${
        isSelected
          ? "bg-gio-500 text-white"
          : isToday
          ? "bg-gio-100 text-gio-700"
          : "hover:bg-navy-100 text-gray-700"
      }`}
      aria-label={day.toLocaleDateString("he-IL")}
      aria-pressed={isSelected}
    >
      <span>{day.getDate()}</span>
      {dots.length > 0 && (
        <div className="flex gap-0.5 mt-0.5">
          {dots.slice(0, 3).map((color, i) => (
            <span key={i} className={`w-1 h-1 rounded-full ${isSelected ? "bg-white" : color}`} />
          ))}
        </div>
      )}
    </button>
  );
}

function SelectedDayPanel({ day, items }: { day: Date; items: DeadlineItem[] }) {
  const dayLabel = day.toLocaleDateString("he-IL", { weekday: "long", day: "numeric", month: "long" });

  return (
    <div className="mt-3 border-t border-navy-100 pt-3" dir="rtl">
      <p className="text-xs font-semibold text-gray-500 mb-2">{dayLabel}</p>
      {items.length === 0 ? (
        <p className="text-sm text-slate-400">{he.timeline.calendarNoEvents}</p>
      ) : (
        <div className="flex flex-col gap-2">
          {items.map((item) => {
            const typeLabel = he.timeline.types[item.type as keyof typeof he.timeline.types] ?? item.type;
            const timeFmt = new Date(item.due_date).toLocaleTimeString("he-IL", {
              hour: "2-digit",
              minute: "2-digit",
            });
            const typeColors: Record<string, string> = {
              assignment: "bg-blue-100 text-blue-700",
              exam: "bg-red-100 text-red-700",
              lecture: "bg-green-100 text-green-700",
              announcement: "bg-gray-100 text-gray-600",
            };
            const badgeColor = typeColors[item.type] ?? "bg-gray-100 text-gray-600";
            return (
              <div
                key={item.id}
                className={`bg-white rounded-xl border px-3 py-2 flex flex-col gap-1 ${
                  item.is_urgent ? "border-urgent shadow-sm shadow-red-100" : "border-navy-100"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-gray-800 truncate flex-1">{item.title}</p>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0 ${badgeColor}`}>
                    {typeLabel}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>{timeFmt}</span>
                  <span className="text-slate-300">·</span>
                  <span className="text-slate-500 truncate">{item.course_name}</span>
                  <span className="text-slate-300">·</span>
                  <span className="text-slate-400">{SOURCE_LABELS[item.source] ?? item.source}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function CalendarView({ items }: CalendarViewProps) {
  const today = new Date();
  const [current, setCurrent] = useState<MonthYear>({ year: today.getFullYear(), month: today.getMonth() });
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);

  const goToPrev = () =>
    setCurrent(({ year, month }) => (month === 0 ? { year: year - 1, month: 11 } : { year, month: month - 1 }));
  const goToNext = () =>
    setCurrent(({ year, month }) => (month === 11 ? { year: year + 1, month: 0 } : { year, month: month + 1 }));

  const cells = buildCalendarGrid(current.year, current.month);

  const handleDaySelect = (day: Date) => {
    setSelectedDay((prev) => (prev && isSameDay(prev, day) ? null : day));
  };

  const selectedItems = selectedDay ? deadlinesForDay(items, selectedDay) : [];

  return (
    <div className="px-4 pb-6" dir="rtl">
      <MonthHeader current={current} onPrev={goToPrev} onNext={goToNext} />

      <div className="grid grid-cols-7 mb-1">
        {he.timeline.calendarDayNames.map((name) => (
          <div key={name} className="text-center text-[10px] font-medium text-slate-400 py-1">
            {name}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-0.5">
        {cells.map((day, idx) => {
          const dayItems = day ? deadlinesForDay(items, day) : [];
          const dots = dayItems.map((i) => dotColorForType(i.type));
          const isSelected = !!(day && selectedDay && isSameDay(day, selectedDay));
          const isToday = !!(day && isSameDay(day, today));
          return (
            <DayCell
              key={idx}
              day={day}
              dots={dots}
              isSelected={isSelected}
              isToday={isToday}
              onSelect={() => day && handleDaySelect(day)}
            />
          );
        })}
      </div>

      {selectedDay && <SelectedDayPanel day={selectedDay} items={selectedItems} />}
    </div>
  );
}
