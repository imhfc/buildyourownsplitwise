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
  auth_provider: string;
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
    }
  )
);

// Zustand 5 的 toThenable 對 localStorage 是同步執行，persist 選項中的 hydration 回呼
// 在 create() 完成前就被呼叫，此時 useAuthStore 還是 undefined，setState 會靜默失敗。
// 正確做法：store 建立後再用 onFinishHydration 註冊，並補上同步情境的檢查。
useAuthStore.persist.onFinishHydration(() => {
  useAuthStore.setState({ hasHydrated: true });
});
if (useAuthStore.persist.hasHydrated()) {
  useAuthStore.setState({ hasHydrated: true });
}
