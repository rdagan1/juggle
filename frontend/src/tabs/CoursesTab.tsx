import { useEffect, useState } from "react";
import { coursesApi, type CourseItem, type GioAttachment } from "../api/client";
import { he } from "../i18n/he";
import { type TabId } from "../components/TabNavigator";
import { ThreeDotMenu } from "../components/ThreeDotMenu";

interface CoursesTabProps {
  onNavigate: (tab: TabId, courseId?: string) => void;
  onAskGio?: (attachment: GioAttachment) => void;
}

function courseToAttachment(course: CourseItem): GioAttachment {
  return {
    id: course.id,
    type: "course",
    title: course.name,
    subtitle: course.code ?? undefined,
  };
}

function CourseCard({
  course,
  onNavigate,
  onAskGio,
  onDelete,
}: {
  course: CourseItem;
  onNavigate: (tab: TabId, courseId: string) => void;
  onAskGio?: (attachment: GioAttachment) => void;
  onDelete: (id: string) => void;
}) {
  const nextExamDate = course.next_exam
    ? new Date(course.next_exam.due_date).toLocaleDateString("he-IL", {
        day: "numeric",
        month: "numeric",
      })
    : null;

  const nextDeadlineDate = course.next_deadline
    ? new Date(course.next_deadline.due_date).toLocaleDateString("he-IL", {
        day: "numeric",
        month: "numeric",
      })
    : null;

  return (
    <div className="bg-white rounded-xl border border-navy-100 overflow-hidden" dir="rtl">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-navy-50">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm text-gray-800">{course.name}</p>
            {course.code && (
              <p className="text-[10px] text-slate-400 mt-0.5">{course.code}</p>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {course.grade_average != null && (
              <div className="text-left">
                <p className="text-[10px] text-slate-400">{he.courses.gradeAverage}</p>
                <p className="font-bold text-gio-600 text-sm">{course.grade_average.toFixed(1)}%</p>
              </div>
            )}
            <ThreeDotMenu
              items={[
                {
                  label: he.menu.delete,
                  onClick: () => onDelete(course.id),
                  danger: true,
                },
              ]}
            />
          </div>
        </div>
      </div>

      {/* Upcoming events */}
      <div className="px-4 py-3 flex flex-col gap-2">
        {course.next_exam && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500">{he.courses.nextExam}</span>
            <div className="flex items-center gap-1.5">
              {course.next_exam.moed && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-purple-100 text-purple-700">
                  מועד {course.next_exam.moed}
                </span>
              )}
              <span className="font-medium text-gray-700">{nextExamDate}</span>
            </div>
          </div>
        )}

        {course.next_deadline && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500">{he.courses.nextDeadline}</span>
            <span className="font-medium text-gray-700">{nextDeadlineDate}</span>
          </div>
        )}

        {course.pending_count === 0 && !course.next_exam && !course.next_deadline && (
          <p className="text-xs text-slate-400">אין מטלות פתוחות</p>
        )}
      </div>

      {/* Filter buttons */}
      <div className="px-4 pb-3 flex gap-2">
        <button
          onClick={() => onNavigate("timeline", course.id)}
          className="flex-1 py-1.5 rounded-lg border border-navy-200 text-xs text-slate-600 hover:bg-navy-50 transition-colors min-h-[32px]"
        >
          {he.courses.filterTimeline}
        </button>
        <button
          onClick={() => onNavigate("grades", course.id)}
          className="flex-1 py-1.5 rounded-lg border border-navy-200 text-xs text-slate-600 hover:bg-navy-50 transition-colors min-h-[32px]"
        >
          {he.courses.filterGrades}
        </button>
        <button
          onClick={() => { onAskGio?.(courseToAttachment(course)); onNavigate("gio"); }}
          className="flex-1 py-1.5 rounded-lg border border-gio-100 text-xs text-gio-600 hover:bg-gio-50 transition-colors min-h-[32px]"
        >
          שאל/י את Gio
        </button>
      </div>
    </div>
  );
}

export function CoursesTab({ onNavigate, onAskGio }: CoursesTabProps) {
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    coursesApi
      .get()
      .then(({ data }) => setCourses(data.courses))
      .catch(() => setError(he.errors.generic))
      .finally(() => setIsLoading(false));
  }, []);

  const handleDelete = (id: string) => {
    coursesApi
      .delete(id)
      .then(() => setCourses((prev) => prev.filter((c) => c.id !== id)))
      .catch(() => setError(he.errors.generic));
  };

  return (
    <div
      id="panel-courses"
      role="tabpanel"
      aria-label={he.tabs.courses}
      className="flex flex-col h-full bg-navy-50 overflow-y-auto"
      dir="rtl"
    >
      <header className="px-4 pt-5 pb-3">
        <h1 className="text-xl font-bold text-gray-800">{he.courses.title}</h1>
      </header>

      {isLoading && (
        <div className="flex-1 flex items-center justify-center text-slate-400">טוען...</div>
      )}

      {error && (
        <div className="mx-4 p-3 rounded-xl bg-red-50 text-red-600 text-sm">{error}</div>
      )}

      {!isLoading && !error && courses.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
          {he.courses.noCourses}
        </div>
      )}

      <div className="flex flex-col gap-3 px-4 pb-6">
        {courses.map((course) => (
          <CourseCard
            key={course.id}
            course={course}
            onNavigate={onNavigate}
            onAskGio={onAskGio}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
