import { useCallback, useEffect } from "react";
import { Platform, View } from "react-native";
import { Tabs, useFocusEffect, usePathname } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTranslation } from "react-i18next";
import { Users, SquaresFour, ClockCounterClockwise, UserCircle } from "phosphor-react-native";
import { useTheme, COLOR_SCHEMES } from "~/lib/theme";
import { useNotificationStore } from "~/stores/notification";
import { usePendingSettlementsStore } from "~/stores/pending-settlements";
import { useAuthStore } from "~/stores/auth";

export default function TabsLayout() {
  const { t } = useTranslation();
  const { isDark, colorScheme } = useTheme();
  const rawInsets = useSafeAreaInsets();
  // Web 上 useSafeAreaInsets 可能回傳 0（viewport 未設 viewport-fit=cover），
  // 給予最低 8px 底部間距，避免 tab bar 被手機瀏覽器工具列遮擋
  const bottomInset = Platform.OS === "web" ? Math.max(rawInsets.bottom, 8) : rawInsets.bottom;
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount);
  const pendingSettlementCount = usePendingSettlementsStore((s) => s.count);
  const fetchPendingSettlementCount = usePendingSettlementsStore((s) => s.fetchCount);

  const scheme = COLOR_SCHEMES.find((s) => s.id === colorScheme) ?? COLOR_SCHEMES[0];
  const activeTint = isDark ? scheme.preview.dark : scheme.preview.light;
  const inactiveTint = isDark ? "#525252" : "#A3A3A3";
  const bgColor = isDark ? scheme.background.dark : scheme.background.light;

  useFocusEffect(
    useCallback(() => {
      if (isAuthenticated) {
        fetchUnreadCount();
        fetchPendingSettlementCount();
      }
    }, [isAuthenticated, fetchUnreadCount, fetchPendingSettlementCount])
  );

  useEffect(() => {
    if (!isAuthenticated) return;
    const interval = setInterval(() => {
      fetchUnreadCount();
      fetchPendingSettlementCount();
    }, 30_000);
    return () => clearInterval(interval);
  }, [isAuthenticated, fetchUnreadCount, fetchPendingSettlementCount]);

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: activeTint,
        tabBarInactiveTintColor: inactiveTint,
        tabBarStyle: {
          backgroundColor: bgColor,
          borderTopWidth: 1,
          borderTopColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)",
          height: 52 + bottomInset,
          paddingBottom: bottomInset,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "500",
          letterSpacing: 0.2,
        },
        headerStyle: {
          backgroundColor: bgColor,
        },
        headerTintColor: isDark ? "#FAFAFA" : "#171717",
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="friends"
        options={{
          title: t("friends"),
          tabBarIcon: ({ color, focused }) => (
            <Users size={20} color={color} weight={focused ? "fill" : "light"} />
          ),
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: t("groups"),
          tabBarIcon: ({ color, focused }) => (
            <SquaresFour size={20} color={color} weight={focused ? "fill" : "light"} />
          ),
          tabBarBadge: pendingSettlementCount > 0 ? pendingSettlementCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: isDark ? "#525252" : "#171717",
            color: "#FFFFFF",
            fontSize: 10,
            fontWeight: "600",
            minWidth: 16,
            height: 16,
            lineHeight: 16,
            borderRadius: 8,
          },
        }}
      />
      <Tabs.Screen
        name="activities"
        options={{
          title: t("activities"),
          tabBarIcon: ({ color, focused }) => (
            <ClockCounterClockwise size={20} color={color} weight={focused ? "fill" : "light"} />
          ),
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: isDark ? "#525252" : "#171717",
            color: "#FFFFFF",
            fontSize: 10,
            fontWeight: "600",
            minWidth: 16,
            height: 16,
            lineHeight: 16,
            borderRadius: 8,
          },
        }}
      />
      <Tabs.Screen
        name="account"
        options={{
          title: t("account"),
          tabBarIcon: ({ color, focused }) => (
            <UserCircle size={20} color={color} weight={focused ? "fill" : "light"} />
          ),
        }}
      />
    </Tabs>
  );
}
