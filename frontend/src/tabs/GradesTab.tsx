import { useEffect, useState } from "react";
import { gradesApi, type CourseGrades, type GradeItem, type GioAttachment } from "../api/client";
import { he, SOURCE_LABELS } from "../i18n/he";
import { type TabId } from "../components/TabNavigator";
import { ThreeDotMenu } from "../components/ThreeDotMenu";

interface GradesTabProps {
  onNavigate: (tab: TabId) => void;
  filterCourseId?: string;
  onFilterCourseName?: (name: string) => void;
  onAskGio?: (attachment: GioAttachment) => void;
}

function courseGradesToAttachment(course: CourseGrades): GioAttachment {
  return {
    id: course.course_id,
    type: "grade",
    title: course.course_name,
    subtitle: `ממוצע ${course.average.toFixed(1)}%`,
  };
}

function TrendArrow({ grades }: { grades: { percentage: number | null }[] }) {
  if (grades.length < 2) return null;
  const last = grades[0].percentage ?? 0;
  const prev = grades[1].percentage ?? 0;
  const diff = last - prev;
  if (Math.abs(diff) < 1) return null;
  return (
    <span className={`text-xs font-bold ${diff > 0 ? "text-green-600" : "text-red-500"}`} aria-label={`${diff > 0 ? "עלייה" : "ירידה"} של ${Math.abs(diff).toFixed(1)} נקודות`}>
      {diff > 0 ? "↑" : "↓"} {Math.abs(diff).toFixed(1)}
    </span>
  );
}

function CourseSection({
  course,
  onGioReport,
  onDeleteGrade,
}: {
  course: CourseGrades;
  onGioReport: (attachment: GioAttachment) => void;
  onDeleteGrade: (gradeId: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);

  return (
    <section className="bg-white rounded-xl border border-navy-100 overflow-hidden" dir="rtl">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full px-4 py-3 flex items-center justify-between min-h-[52px]"
        aria-expanded={expanded}
        aria-label={`${course.course_name} — ממוצע ${course.average}%`}
      >
        <div className="flex flex-col items-start gap-0.5">
          <span className="font-semibold text-sm text-gray-800">{course.course_name}</span>
          {course.course_code && (
            <span className="text-[10px] text-slate-400">{course.course_code}</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="text-left">
            <p className="text-xs text-slate-400">{he.grades.average}</p>
            <p className="font-bold text-gio-600">{course.average.toFixed(1)}%</p>
          </div>
          <span className="text-gray-300 text-sm">{expanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-50 divide-y divide-navy-50">
          {course.grades.map((g: GradeItem, idx: number) => (
            <div key={g.id} className="px-4 py-3 flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <p className="text-sm text-gray-700">{g.assignment_title ?? "ציון"}</p>
                <p className="text-[10px] text-slate-400">
                  {new Date(g.received_at).toLocaleDateString("he-IL")} ·{" "}
                  {SOURCE_LABELS[g.source] ?? g.source}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {idx === 0 && <TrendArrow grades={course.grades} />}
                <div className="text-left">
                  <p className="font-bold text-gray-800">{g.grade}</p>
                  <p className="text-[10px] text-slate-400">מתוך {g.max_grade}</p>
                </div>
                {g.percentage != null && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    g.percentage >= 85 ? "bg-green-100 text-green-700" :
                    g.percentage >= 70 ? "bg-blue-100 text-blue-700" :
                    "bg-red-100 text-red-700"
                  }`}>
                    {g.percentage.toFixed(0)}%
                  </span>
                )}
                <ThreeDotMenu
                  items={[
                    {
                      label: he.menu.delete,
                      onClick: () => onDeleteGrade(g.id),
                      danger: true,
                    },
                  ]}
                />
              </div>
            </div>
          ))}

          <div className="px-4 py-2 flex justify-end">
            <button
              onClick={() => onGioReport(courseGradesToAttachment(course))}
              className="text-xs text-gio-500 hover:underline min-h-[32px]"
              aria-label={he.grades.reportToGio}
            >
              {he.grades.reportToGio}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export function GradesTab({ onNavigate, filterCourseId, onFilterCourseName, onAskGio }: GradesTabProps) {
  const [courses, setCourses] = useState<CourseGrades[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    gradesApi
      .get(filterCourseId)
      .then(({ data }) => {
        setCourses(data.courses);
        if (filterCourseId && data.courses.length > 0 && onFilterCourseName) {
          onFilterCourseName(data.courses[0].course_name);
        }
      })
      .catch(() => setError(he.errors.generic))
      .finally(() => setIsLoading(false));
  }, [filterCourseId]);

  const handleDeleteGrade = (gradeId: string) => {
    gradesApi
      .delete(gradeId)
      .then(() => {
        setCourses((prev) =>
          prev
            .map((c) => ({
              ...c,
              grades: c.grades.filter((g) => g.id !== gradeId),
            }))
            .filter((c) => c.grades.length > 0),
        );
      })
      .catch(() => setError(he.errors.generic));
  };

  return (
    <div
      id="panel-grades"
      role="tabpanel"
      aria-label={he.tabs.grades}
      className="flex flex-col h-full bg-navy-50 overflow-y-auto"
      dir="rtl"
    >
      <header className="px-4 pt-5 pb-3">
        <h1 className="text-xl font-bold text-gray-800">{he.grades.title}</h1>
      </header>

      {isLoading && (
        <div className="flex-1 flex items-center justify-center text-slate-400">טוען...</div>
      )}

      {error && (
        <div className="mx-4 p-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>
      )}

      {!isLoading && !error && courses.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
          {he.grades.noCourses}
        </div>
      )}

      <div className="flex flex-col gap-3 px-4 pb-6">
        {courses.map((course) => (
          <CourseSection
            key={course.course_id}
            course={course}
            onGioReport={(attachment) => { onAskGio?.(attachment); onNavigate("gio"); }}
            onDeleteGrade={handleDeleteGrade}
          />
        ))}
      </div>
    </div>
  );
}
