import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

// Web 用原生 localStorage（同步，不會掛住）；Native 用 AsyncStorage
const storage = createJSONStorage(() =>
  Platform.OS === "web" ? localStorage : AsyncStorage
);

interface User {
  id: string;
  email: string | null;
  display_name: string;
  avatar_url: string | null;
  preferred_currency: string;
  locale: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  hasHydrated: boolean;
  setAuth: (token: string, refreshToken: string, user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      hasHydrated: false,

      setAuth: (token, refreshToken, user) =>
        set({ token, refreshToken, user, isAuthenticated: true }),

      setTokens: (token, refreshToken) =>
        set({ token, refreshToken }),

      logout: () =>
        set({ token: null, refreshToken: null, user: null, isAuthenticated: false }),

      updateUser: (partial) =>
        set({ user: { ...get().user!, ...partial } }),
    }),
    {
      name: "auth-storage",
      storage,
      // hasHydrated 是 runtime 狀態，不需要 persist
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => () => {
        useAuthStore.setState({ hasHydrated: true });
      },
    }
  )
);
