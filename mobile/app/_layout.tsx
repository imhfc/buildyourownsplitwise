import "../global.css";
import "../i18n";
import { useEffect } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { ThemeProvider as NavThemeProvider, DarkTheme, DefaultTheme } from "@react-navigation/native";
import { ThemeProvider, useTheme } from "~/lib/theme";
import { useAuthStore } from "../stores/auth";

const SCHEME_CLASS: Record<string, string> = {
  blue: "",
  green: "scheme-green",
  purple: "scheme-purple",
  warm: "scheme-warm",
  red: "scheme-red",
  orange: "scheme-orange",
  rose: "scheme-rose",
  teal: "scheme-teal",
  amber: "scheme-amber",
  slate: "scheme-slate",
};

function InnerLayout() {
  const { isDark, colorScheme } = useTheme();
  const router = useRouter();
  const segments = useSegments();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);

  useEffect(() => {
    if (!hasHydrated) return;

    const inAuthGroup = segments[0] === "(auth)";
    const inTabsGroup = segments[0] === "(tabs)";
    const inGroupPage = segments[0] === "group";

    if (!isAuthenticated && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (isAuthenticated && !inTabsGroup && !inGroupPage) {
      // 涵蓋 index.tsx（spinner）和 auth 頁面，都導向 tabs
      router.replace("/(tabs)");
    }
  }, [isAuthenticated, hasHydrated, segments]);

  return (
    <NavThemeProvider value={isDark ? DarkTheme : DefaultTheme}>
      <View className={`${isDark ? "dark" : ""} ${SCHEME_CLASS[colorScheme] || ""} flex-1`.trim()}>
        <View className="flex-1 bg-background">
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: "transparent" },
            }}
          >
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(tabs)" options={{ headerShown: false, title: "返回" }} />
            <Stack.Screen
              name="group/[id]"
              options={{
                headerShown: true,
                title: "",
                headerBackTitle: "返回",
                headerStyle: { backgroundColor: isDark ? "#09090B" : "#FFFFFF" },
                headerTintColor: isDark ? "#FAFAFA" : "#09090B",
                headerShadowVisible: false,
              }}
            />
          </Stack>
          <StatusBar style={isDark ? "light" : "dark"} />
        </View>
      </View>
    </NavThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ThemeProvider>
        <InnerLayout />
      </ThemeProvider>
    </GestureHandlerRootView>
  );
}
