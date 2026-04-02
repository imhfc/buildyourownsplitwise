import { createContext, useContext, useEffect, useState } from "react";
import { useColorScheme as useRNColorScheme } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

type Theme = "light" | "dark" | "system";
export type ColorScheme = "blue" | "green" | "purple" | "warm" | "coral" | "slate";

export const COLOR_SCHEMES: {
  id: ColorScheme;
  labelKey: string;
  preview: { light: string; dark: string };
}[] = [
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
}

const ThemeCtx = createContext<ThemeContext>({
  theme: "system",
  isDark: false,
  setTheme: () => {},
  toggleTheme: () => {},
  colorScheme: "blue",
  setColorScheme: () => {},
});

const THEME_KEY = "byosw-theme";
const COLOR_SCHEME_KEY = "byosw-color-scheme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useRNColorScheme();
  const [theme, setThemeState] = useState<Theme>("system");
  const [colorScheme, setColorSchemeState] = useState<ColorScheme>("blue");

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

  const setTheme = (t: Theme) => {
    setThemeState(t);
    AsyncStorage.setItem(THEME_KEY, t);
  };

  const setColorScheme = (s: ColorScheme) => {
    setColorSchemeState(s);
    AsyncStorage.setItem(COLOR_SCHEME_KEY, s);
  };

  const isDark =
    theme === "system" ? systemScheme === "dark" : theme === "dark";

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <ThemeCtx.Provider value={{ theme, isDark, setTheme, toggleTheme, colorScheme, setColorScheme }}>
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
  if (colorScheme !== "blue") parts.push(`scheme-${colorScheme}`);
  return parts.join(" ");
}
