import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useColorScheme as useRNColorScheme } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { authAPI } from "../services/api";
import { useAuthStore } from "../stores/auth";

type Theme = "light" | "dark" | "system";
export type ColorScheme = "byosw" | "blue" | "green" | "purple" | "warm" | "coral" | "slate";

export const COLOR_SCHEMES: {
  id: ColorScheme;
  labelKey: string;
  preview: { light: string; dark: string };
}[] = [
  { id: "byosw",  labelKey: "scheme_byosw",  preview: { light: "#0F172A", dark: "#E2E8F0" } },
  { id: "blue",   labelKey: "scheme_blue",   preview: { light: "#3B82F6", dark: "#60A5FA" } },
  { id: "green",  labelKey: "scheme_green",  preview: { light: "#5BC5A7", dark: "#4DB899" } },
  { id: "purple", labelKey: "scheme_purple", preview: { light: "#6E4CE5", dark: "#8B6CF7" } },
  { id: "warm",   labelKey: "scheme_warm",   preview: { light: "#1B4D3E", dark: "#3D8B74" } },
  { id: "coral",  labelKey: "scheme_coral",  preview: { light: "#D96A3E", dark: "#C08070" } },
  { id: "slate",  labelKey: "scheme_slate",  preview: { light: "#64748B", dark: "#94A3B8" } },
];

interface ThemeContext {
  theme: Theme;
  isDark: boolean;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  colorScheme: ColorScheme;
  setColorScheme: (scheme: ColorScheme) => void;
  /** 登入後從後端 user 物件同步主題設定到本地 */
  syncFromUser: (user: { color_scheme?: string; theme_mode?: string }) => void;
}

const ThemeCtx = createContext<ThemeContext>({
  theme: "system",
  isDark: false,
  setTheme: () => {},
  toggleTheme: () => {},
  colorScheme: "blue",
  setColorScheme: () => {},
  syncFromUser: () => {},
});

const THEME_KEY = "byosw-theme";
const COLOR_SCHEME_KEY = "byosw-color-scheme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useRNColorScheme();
  const [theme, setThemeState] = useState<Theme>("system");
  const [colorScheme, setColorSchemeState] = useState<ColorScheme>("byosw");

  useEffect(() => {
    Promise.all([
      AsyncStorage.getItem(THEME_KEY),
      AsyncStorage.getItem(COLOR_SCHEME_KEY),
    ]).then(([savedTheme, savedScheme]) => {
      if (savedTheme === "light" || savedTheme === "dark" || savedTheme === "system") {
        setThemeState(savedTheme);
      }
      if (COLOR_SCHEMES.some((s) => s.id === savedScheme)) {
        setColorSchemeState(savedScheme as ColorScheme);
      }
    });
  }, []);

  // 避免初始化載入時觸發後端推送
  const initializedRef = useRef(false);

  const pushToBackend = (patch: Record<string, string>) => {
    if (!initializedRef.current) return;
    const isAuthenticated = useAuthStore.getState().isAuthenticated;
    if (!isAuthenticated) return;
    authAPI.updateMe(patch).catch(() => {
      // 靜默失敗 -- 本地設定已生效，下次登入會再同步
    });
  };

  const setTheme = (t: Theme) => {
    setThemeState(t);
    AsyncStorage.setItem(THEME_KEY, t);
    pushToBackend({ theme_mode: t });
  };

  const setColorScheme = (s: ColorScheme) => {
    setColorSchemeState(s);
    AsyncStorage.setItem(COLOR_SCHEME_KEY, s);
    pushToBackend({ color_scheme: s });
  };

  const syncFromUser = (user: { color_scheme?: string; theme_mode?: string }) => {
    if (user.color_scheme && COLOR_SCHEMES.some((s) => s.id === user.color_scheme)) {
      setColorSchemeState(user.color_scheme as ColorScheme);
      AsyncStorage.setItem(COLOR_SCHEME_KEY, user.color_scheme);
    }
    if (user.theme_mode && (user.theme_mode === "light" || user.theme_mode === "dark" || user.theme_mode === "system")) {
      setThemeState(user.theme_mode as Theme);
      AsyncStorage.setItem(THEME_KEY, user.theme_mode);
    }
  };

  // 初始化完成後才允許推送
  useEffect(() => {
    initializedRef.current = true;
  }, []);

  // 已登入時從後端拉取最新主題設定（處理跨裝置同步）
  const syncedRef = useRef(false);
  const fetchAndSync = () => {
    if (syncedRef.current) return;
    syncedRef.current = true;
    authAPI.getMe().then((res) => syncFromUser(res.data)).catch(() => {
      syncedRef.current = false; // 失敗時允許重試
    });
  };
  useEffect(() => {
    // 訂閱 auth store 變化，等 hydration 完成且已登入才拉設定
    const unsub = useAuthStore.subscribe((state) => {
      if (state.isAuthenticated && state.hasHydrated) fetchAndSync();
    });
    // 也立即檢查一次（Web 上 localStorage hydration 是同步的，subscribe 可能錯過）
    const { isAuthenticated, hasHydrated } = useAuthStore.getState();
    if (isAuthenticated && hasHydrated) fetchAndSync();
    return unsub;
  }, []);

  const isDark =
    theme === "system" ? systemScheme === "dark" : theme === "dark";

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <ThemeCtx.Provider value={{ theme, isDark, setTheme, toggleTheme, colorScheme, setColorScheme, syncFromUser }}>
      {children}
    </ThemeCtx.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeCtx);
}

/** 回传当前主题对应的 NativeWind className（含 dark + scheme-*），用于 Modal 等 portal 场景 */
export function useThemeClassName() {
  const { isDark, colorScheme } = useTheme();
  const parts: string[] = [];
  if (isDark) parts.push("dark");
  if (colorScheme !== "byosw") parts.push(`scheme-${colorScheme}`);
  return parts.join(" ");
}
