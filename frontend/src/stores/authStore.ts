/**
 * Authentication state management with Zustand.
 */
import { create } from "zustand";
import type { User, AuthTokens, LoginCredentials, RegisterData } from "@/types";
import api from "@/lib/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  hydrate: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  // Always start "logged out" so server and initial client render match.
  // Real auth state is hydrated after mount via hydrate() to avoid SSR
  // hydration mismatches.
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post<AuthTokens>("/auth/login/", credentials);
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);
      set({ isAuthenticated: true });
      // Fetch user profile
      const profile = await api.get<User>("/auth/profile/");
      set({ user: profile.data, isLoading: false });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail || "Login failed";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await api.post("/auth/register/", data);
      set({ isLoading: false });
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: Record<string, string[]> } })
        ?.response?.data;
      const msg = errData
        ? Object.values(errData).flat().join(", ")
        : "Registration failed";
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchProfile: async () => {
    try {
      const { data } = await api.get<User>("/auth/profile/");
      set({ user: data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },

  // Called once after mount (client-side) to restore session from storage.
  hydrate: () => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem("access_token")) {
      set({ isAuthenticated: true });
      // Best-effort profile fetch; clears state if the token is invalid.
      api
        .get<User>("/auth/profile/")
        .then(({ data }) => set({ user: data, isAuthenticated: true }))
        .catch(() => set({ user: null, isAuthenticated: false }));
    }
  },

  clearError: () => set({ error: null }),
}));
