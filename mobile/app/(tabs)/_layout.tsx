import { useCallback, useEffect } from "react";
import { Tabs, useFocusEffect, usePathname } from "expo-router";
import { useTranslation } from "react-i18next";
import { UserPlus, Users, Activity, User } from "lucide-react-native";
import { useTheme, COLOR_SCHEMES } from "~/lib/theme";
import { useNotificationStore } from "~/stores/notification";
import { useAuthStore } from "~/stores/auth";

export default function TabsLayout() {
  const { t } = useTranslation();
  const { isDark, colorScheme } = useTheme();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount);

  const scheme = COLOR_SCHEMES.find((s) => s.id === colorScheme) ?? COLOR_SCHEMES[0];
  const activeTint = isDark ? scheme.preview.dark : scheme.preview.light;
  const inactiveTint = isDark ? "#A1A1AA" : "#71717A";

  // 每次 tab layout 獲得焦點時拉取未讀數量
  useFocusEffect(
    useCallback(() => {
      if (isAuthenticated) {
        fetchUnreadCount();
      }
    }, [isAuthenticated, fetchUnreadCount])
  );

  // 定期輪詢未讀數量（每 30 秒）
  useEffect(() => {
    if (!isAuthenticated) return;
    const interval = setInterval(fetchUnreadCount, 30_000);
    return () => clearInterval(interval);
  }, [isAuthenticated, fetchUnreadCount]);

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: activeTint,
        tabBarInactiveTintColor: inactiveTint,
        tabBarStyle: {
          backgroundColor: isDark ? "#09090B" : "#FFFFFF",
          borderTopColor: isDark ? "#27272A" : "#E4E4E7",
          height: 60,
          paddingBottom: 8,
          paddingTop: 4,
        },
        headerStyle: {
          backgroundColor: isDark ? "#09090B" : "#FFFFFF",
        },
        headerTintColor: isDark ? "#FAFAFA" : "#09090B",
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="friends"
        options={{
          title: t("friends"),
          tabBarIcon: ({ color, size }) => (
            <UserPlus size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: t("groups"),
          tabBarIcon: ({ color, size }) => (
            <Users size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="activities"
        options={{
          title: t("activities"),
          tabBarIcon: ({ color, size }) => (
            <Activity size={size} color={color} />
          ),
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: "#EF4444",
            color: "#FFFFFF",
            fontSize: 11,
            fontWeight: "700",
            minWidth: 18,
            height: 18,
            lineHeight: 18,
            borderRadius: 9,
          },
        }}
      />
      <Tabs.Screen
        name="account"
        options={{
          title: t("account"),
          tabBarIcon: ({ color, size }) => (
            <User size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
