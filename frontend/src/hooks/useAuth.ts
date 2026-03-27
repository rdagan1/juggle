import { create } from "zustand";
import { authApi, type TokenResponse } from "../api/client";

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Onboarding registration step
  pendingEmail: string | null;

  login: (email: string, password: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  register: (email: string, name: string) => Promise<{ dev_code?: string }>;
  verify: (email: string, code: string, password: string) => Promise<void>;
  logout: () => void;
  setPendingEmail: (email: string) => void;
}

function storeTokens(tokens: TokenResponse) {
  localStorage.setItem("access_token", tokens.access_token);
  localStorage.setItem("refresh_token", tokens.refresh_token);
}

export const useAuth = create<AuthState>((set) => ({
  accessToken: localStorage.getItem("access_token"),
  isAuthenticated: Boolean(localStorage.getItem("access_token")),
  isLoading: false,
  error: null,
  pendingEmail: null,

  demoLogin: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await authApi.demo();
      storeTokens(data);
      set({ accessToken: data.access_token, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Demo login failed";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await authApi.login(email, password);
      storeTokens(data);
      set({ accessToken: data.access_token, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "שגיאת כניסה";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  register: async (email, name) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await authApi.register(email, name);
      set({ isLoading: false, pendingEmail: email });
      return data;
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "שגיאת הרשמה";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  verify: async (email, code, password) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await authApi.verify(email, code, password);
      storeTokens(data);
      set({ accessToken: data.access_token, isAuthenticated: true, isLoading: false, pendingEmail: null });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "קוד שגוי";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ accessToken: null, isAuthenticated: false });
  },

  setPendingEmail: (email) => set({ pendingEmail: email }),
}));
