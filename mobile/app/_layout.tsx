import "../global.css";
import "../i18n";
import { useEffect } from "react";
import { Platform } from "react-native";
import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { ThemeProvider as NavThemeProvider, DarkTheme, DefaultTheme } from "@react-navigation/native";
import { ThemeProvider, useTheme, COLOR_SCHEMES } from "~/lib/theme";
import { useAuthStore } from "../stores/auth";
import { registerForPushNotifications, setupNotificationHandlers, addNotificationReceivedCallback } from "~/lib/notifications";
import { useNotificationStore } from "~/stores/notification";
import { usePendingSettlementsStore } from "~/stores/pending-settlements";

// Web: 注入 PWA meta tags + viewport-fit + 100dvh + service worker
if (Platform.OS === "web" && typeof document !== "undefined") {
  const head = document.head;

  // viewport-fit=cover 讓 env(safe-area-inset-*) 生效
  const meta = document.querySelector('meta[name="viewport"]');
  if (meta) {
    const content = meta.getAttribute("content") || "";
    if (!content.includes("viewport-fit")) {
      meta.setAttribute("content", content + ", viewport-fit=cover");
    }
  }

  // 100dvh 排除手機瀏覽器工具列高度
  const dvhStyle = document.createElement("style");
  dvhStyle.textContent = "html,body,#root{height:100dvh!important}";
  head.appendChild(dvhStyle);

  // PWA manifest
  const manifestLink = document.createElement("link");
  manifestLink.rel = "manifest";
  manifestLink.href = "/manifest.json";
  head.appendChild(manifestLink);

  // theme-color
  const themeColor = document.createElement("meta");
  themeColor.name = "theme-color";
  themeColor.content = "#171717";
  head.appendChild(themeColor);

  // Apple PWA meta tags
  const appleMeta = document.createElement("meta");
  appleMeta.name = "apple-mobile-web-app-capable";
  appleMeta.content = "yes";
  head.appendChild(appleMeta);

  const appleStatusBar = document.createElement("meta");
  appleStatusBar.name = "apple-mobile-web-app-status-bar-style";
  appleStatusBar.content = "black-translucent";
  head.appendChild(appleStatusBar);

  const appleTitle = document.createElement("meta");
  appleTitle.name = "apple-mobile-web-app-title";
  appleTitle.content = "byosw";
  head.appendChild(appleTitle);

  const appleIcon = document.createElement("link");
  appleIcon.rel = "apple-touch-icon";
  appleIcon.href = "/icon-192.png";
  head.appendChild(appleIcon);

  // Service Worker 註冊
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
  }
}

const SCHEME_CLASS: Record<string, string> = {
  byosw: "",
  blue: "scheme-blue",
  green: "scheme-green",
  purple: "scheme-purple",
  warm: "scheme-warm",
  coral: "scheme-coral",
};

function InnerLayout() {
  const { isDark, colorScheme } = useTheme();
  const scheme = COLOR_SCHEMES.find((s) => s.id === colorScheme) ?? COLOR_SCHEMES[0];
  const primaryColor = isDark ? scheme.preview.dark : scheme.preview.light;
  const router = useRouter();
  const segments = useSegments();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);

  useEffect(() => {
    if (!hasHydrated) return;

    const inAuthGroup = segments[0] === "(auth)";
    const inTabsGroup = segments[0] === "(tabs)";
    const inGroupPage = segments[0] === "group";
    const inJoinPage = segments[0] === "join";
    const inInvitePage = segments[0] === "invite";

    if (!isAuthenticated && !inAuthGroup && !inJoinPage && !inInvitePage) {
      router.replace("/(auth)/login");
    } else if (isAuthenticated && !inTabsGroup && !inGroupPage && !inJoinPage && !inInvitePage) {
      // 登入後檢查是否有待處理的邀請連結
      const pending = useAuthStore.getState().pendingInviteToken;
      if (pending) {
        useAuthStore.getState().setPendingInviteToken(null);
        if (pending.startsWith("email:")) {
          router.replace(`/invite/email/${pending.slice(6)}`);
        } else {
          router.replace(`/join/${pending}`);
        }
      } else {
        router.replace("/(tabs)");
      }
    }
  }, [isAuthenticated, hasHydrated, segments]);

  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount);
  const fetchPendingSettlementCount = usePendingSettlementsStore((s) => s.fetchCount);

  // Push 通知註冊（登入後）
  useEffect(() => {
    if (isAuthenticated && hasHydrated) {
      setupNotificationHandlers();
      registerForPushNotifications().catch(() => {});
    }
  }, [isAuthenticated, hasHydrated]);

  // 收到推播時立即刷新 pending settlements + 未讀活動
  useEffect(() => {
    if (!isAuthenticated || !hasHydrated) return;
    return addNotificationReceivedCallback(() => {
      fetchPendingSettlementCount();
      fetchUnreadCount();
    });
  }, [isAuthenticated, hasHydrated, fetchPendingSettlementCount, fetchUnreadCount]);

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
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="join/[token]"
              options={{ headerShown: false }}
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
    <SafeAreaProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <ThemeProvider>
          <InnerLayout />
        </ThemeProvider>
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}
