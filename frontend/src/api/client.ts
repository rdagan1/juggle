import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Inject token from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.params = { ...config.params, token };
  }
  return config;
});

// Redirect to login on 401
apiClient.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.reload();
    }
    return Promise.reject(err);
  },
);

// ─── Auth ───────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authApi = {
  register: (email: string, name: string) =>
    apiClient.post<{ message: string; dev_code?: string }>("/auth/register", { email, name }),

  verify: (email: string, code: string, password: string) =>
    apiClient.post<TokenResponse>("/auth/verify", { email, code, password }),

  login: (email: string, password: string) =>
    apiClient.post<TokenResponse>("/auth/login", { email, password }),

  googleLogin: () => {
    window.location.href = `${BASE_URL}/auth/google`;
  },

  demo: () => apiClient.get<TokenResponse>("/auth/demo"),
};

// ─── Attachments ─────────────────────────────────────────────────────────────

/** Display metadata for an attached item (chip in the input bar). */
export interface GioAttachment {
  id: string;
  type: "deadline" | "grade" | "course" | "pdf";
  title: string;
  subtitle?: string;
}

/** Minimal reference sent to the backend — backend queries DB for full context. */
export interface AttachmentRef {
  type: string;
  id: string;
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export interface GioButton {
  label: string;
  value: string;
}

export interface GioMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  buttons?: GioButton[] | null;
  navigate_hint?: string | null;
  template_id?: string | null;
  timestamp: string;
  /** Frontend-only: attachments sent with this message (not persisted). */
  _attachments?: GioAttachment[];
}

export const chatApi = {
  getHistory: (page = 1) =>
    apiClient.get<GioMessage[]>("/api/chat/history", { params: { page } }),

  respond: (
    messageId: string | null,
    buttonValue?: string,
    text?: string,
    buttonLabel?: string,
    attachments?: AttachmentRef[],
  ) =>
    apiClient.post<GioMessage>("/api/chat/respond", {
      message_id: messageId,
      button_value: buttonValue,
      button_label: buttonLabel,
      text,
      attachments: attachments ?? [],
    }),
};

// ─── Upload ──────────────────────────────────────────────────────────────────

export const uploadApi = {
  uploadPdf: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post<{ document_id: string; status: string }>("/api/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ─── Timeline ────────────────────────────────────────────────────────────────

export interface DeadlineItem {
  id: string;
  course_name: string;
  course_code: string | null;
  type: string;
  title: string;
  due_date: string;
  status: string;
  needs_review: boolean;
  estimated_hours: number | null;
  is_urgent: boolean;
  moed: string | null;
  source: string;
}

export const timelineApi = {
  get: (window = 30, courseId?: string) =>
    apiClient.get<{ items: DeadlineItem[]; total: number }>("/api/timeline", {
      params: { window, ...(courseId ? { course_id: courseId } : {}) },
    }),
};

// ─── Courses ─────────────────────────────────────────────────────────────────

export interface CourseItem {
  id: string;
  name: string;
  code: string | null;
  semester: string | null;
  pending_count: number;
  grade_average: number | null;
  next_exam: { id: string; title: string; due_date: string; moed: string | null } | null;
  next_deadline: { id: string; title: string; due_date: string; type: string } | null;
}

export const coursesApi = {
  get: () => apiClient.get<{ courses: CourseItem[] }>("/api/courses"),
};

// ─── Grades ──────────────────────────────────────────────────────────────────

export interface GradeItem {
  id: string;
  assignment_title: string | null;
  grade: number;
  max_grade: number;
  percentage: number | null;
  grade_type: string;
  source: string;
  received_at: string;
}

export interface CourseGrades {
  course_id: string;
  course_name: string;
  course_code: string | null;
  grades: GradeItem[];
  average: number;
}

export const gradesApi = {
  get: (courseId?: string) =>
    apiClient.get<{ courses: CourseGrades[] }>("/api/grades", {
      params: courseId ? { course_id: courseId } : {},
    }),
};

// ─── Emails ──────────────────────────────────────────────────────────────────

export interface EmailItem {
  id: string;
  subject: string | null;
  sender: string | null;
  received_at: string;
  parse_status: string;
  attachment_count: number;
  forwarded_at: string | null;
}

export const emailsApi = {
  get: (page = 1) =>
    apiClient.get<{ emails: EmailItem[] }>("/api/emails", { params: { page } }),
};

// ─── Settings ────────────────────────────────────────────────────────────────

export interface UserSettings {
  virtual_email: string | null;
  name: string | null;
  email: string;
  preferences: Record<string, unknown>;
  has_calendar: boolean;
  has_work_calendar: boolean;
  onboarding_completed: boolean;
  onboarding_step: number;
}

export const settingsApi = {
  get: () => apiClient.get<UserSettings>("/api/settings"),
  update: (prefs: Record<string, unknown>) => apiClient.patch("/api/settings", prefs),
  deleteAccount: () => apiClient.delete("/api/settings/account"),
  getManualUpdates: () => apiClient.get("/api/settings/manual-updates"),
};
