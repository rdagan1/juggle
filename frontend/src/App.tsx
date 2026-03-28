import { useCallback, useEffect, useRef, useState } from "react";
import { AuthScreen } from "./components/AuthScreen";
import { AppHeader } from "./components/AppHeader";
import { TabNavigator, type TabId } from "./components/TabNavigator";
import { GioTab } from "./tabs/GioTab";
import { TimelineTab } from "./tabs/TimelineTab";
import { GradesTab } from "./tabs/GradesTab";
import { CoursesTab } from "./tabs/CoursesTab";
import { EmailsTab } from "./tabs/EmailsTab";
import { SettingsTab } from "./tabs/SettingsTab";
import { useAuth } from "./hooks/useAuth";
import { settingsApi, uploadApi, type GioAttachment } from "./api/client";
import { he } from "./i18n/he";

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

function App() {
  const { isAuthenticated, demoLogin } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>("gio");
  const [userId, setUserId] = useState<string | null>(null);
  const [unreadEmails, setUnreadEmails] = useState(0);
  const [unreadGrades, setUnreadGrades] = useState(0);
  const [filterCourseId, setFilterCourseId] = useState<string | undefined>();
  const [filterCourseName, setFilterCourseName] = useState<string | undefined>();
  const [pendingAttachments, setPendingAttachments] = useState<GioAttachment[]>([]);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (DEMO_MODE && !isAuthenticated) {
      demoLogin().catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    settingsApi.get().then(() => {
      const token = localStorage.getItem("access_token");
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split(".")[1]));
          setUserId(payload.sub);
        } catch {
          // ignore
        }
      }
    });
  }, [isAuthenticated]);

  // Clear filter when navigating away from timeline/grades manually
  const handleTabChange = (tab: TabId) => {
    if (tab !== "timeline" && tab !== "grades") {
      setFilterCourseId(undefined);
      setFilterCourseName(undefined);
    }
    setActiveTab(tab);
  };

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  const navigate = (tab: string, courseId?: string) => {
    const t = tab as TabId;
    if (courseId) {
      setFilterCourseId(courseId);
    } else {
      setFilterCourseId(undefined);
      setFilterCourseName(undefined);
    }
    setActiveTab(t);
  };

  const clearFilter = () => {
    setFilterCourseId(undefined);
    setFilterCourseName(undefined);
  };

  const attachToGio = (attachment: GioAttachment) => {
    setPendingAttachments((prev) => {
      if (prev.some((a) => a.id === attachment.id)) return prev;
      return [...prev, attachment];
    });
  };

  // Poll parse status for any pending PDF attachments every 2s
  useEffect(() => {
    const pendingPdfs = pendingAttachments.filter(
      (a) => a.type === "pdf" && a.parseStatus === "pending"
    );

    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    if (pendingPdfs.length === 0) return;

    pollingRef.current = setInterval(async () => {
      for (const att of pendingPdfs) {
        try {
          const { data } = await uploadApi.getStatus(att.id);
          if (data.parse_status !== "pending") {
            setPendingAttachments((prev) =>
              prev.map((a) => (a.id === att.id ? { ...a, parseStatus: data.parse_status } : a))
            );
          }
        } catch {
          // ignore transient errors
        }
      }
    }, 2000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [pendingAttachments]);

  const removeAttachment = useCallback((id: string) => {
    setPendingAttachments((prev) => {
      const att = prev.find((a) => a.id === id);
      if (att?.type === "pdf" && att.parseStatus === "pending") {
        uploadApi.cancel(id).catch(() => {});
      }
      return prev.filter((a) => a.id !== id);
    });
  }, []);

  // Resolve filter course name from CoursesTab callback
  const navigateWithCourse = (tab: TabId, courseId?: string) => {
    navigate(tab, courseId);
  };

  return (
    <div
      className="flex flex-col h-dvh max-w-md mx-auto bg-navy-50 overflow-hidden"
      dir="rtl"
      lang="he"
    >
      <AppHeader />

      {/* Active filter banner */}
      {filterCourseId && filterCourseName && (
        <div className="bg-gio-50 border-b border-gio-100 px-4 py-1.5 flex items-center justify-between" dir="rtl">
          <span className="text-xs text-gio-600 font-medium">
            {he.courses.filteredBy.replace("{name}", filterCourseName)}
          </span>
          <button
            onClick={clearFilter}
            className="text-xs text-gio-500 hover:underline min-h-[28px] px-2"
          >
            {he.courses.clearFilter}
          </button>
        </div>
      )}

      {/* Tab panels */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "gio" && userId && (
          <GioTab
            userId={userId}
            onNavigate={navigate}
            attachments={pendingAttachments}
            onAddAttachment={attachToGio}
            onRemoveAttachment={removeAttachment}
          />
        )}
        {activeTab === "timeline" && (
          <TimelineTab
            onNavigate={navigate}
            filterCourseId={filterCourseId}
            onFilterCourseName={setFilterCourseName}
            onAskGio={(a) => { attachToGio(a); navigate("gio"); }}
          />
        )}
        {activeTab === "grades" && (
          <GradesTab
            onNavigate={navigate}
            filterCourseId={filterCourseId}
            onFilterCourseName={setFilterCourseName}
            onAskGio={(a) => { attachToGio(a); navigate("gio"); }}
          />
        )}
        {activeTab === "courses" && (
          <CoursesTab
            onNavigate={navigateWithCourse}
            onAskGio={(a) => { attachToGio(a); navigate("gio"); }}
          />
        )}
        {activeTab === "emails" && <EmailsTab />}
        {activeTab === "settings" && <SettingsTab />}
      </main>

      {/* Bottom tab bar */}
      <TabNavigator
        activeTab={activeTab}
        onTabChange={handleTabChange}
        badges={{
          emails: unreadEmails,
          grades: unreadGrades,
        }}
      />
    </div>
  );
}

export default App;
