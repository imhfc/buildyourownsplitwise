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

function InnerLayout() {
  const { isDark } = useTheme();
  const router = useRouter();
  const segments = useSegments();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);

  useEffect(() => {
    if (!hasHydrated) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!isAuthenticated && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (isAuthenticated && inAuthGroup) {
      router.replace("/(tabs)");
    }
  }, [isAuthenticated, hasHydrated, segments]);

  return (
    <NavThemeProvider value={isDark ? DarkTheme : DefaultTheme}>
      <View className={isDark ? "dark flex-1" : "flex-1"}>
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
