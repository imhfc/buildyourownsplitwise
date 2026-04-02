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
          backgroundColor: isDark ? "#101318" : "#FFFFFF",
          borderTopColor: isDark ? "#1F2937" : "#E4E4E7",
          height: 52,
          paddingBottom: 4,
          paddingTop: 2,
        },
        tabBarIconStyle: {
          marginBottom: -2,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          marginTop: -2,
        },
        headerStyle: {
          backgroundColor: isDark ? "#101318" : "#FFFFFF",
        },
        headerTintColor: isDark ? "#FAFAFA" : "#101318",
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="friends"
        options={{
          title: t("friends"),
          tabBarIcon: ({ color }) => (
            <UserPlus size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: t("groups"),
          tabBarIcon: ({ color }) => (
            <Users size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="activities"
        options={{
          title: t("activities"),
          tabBarIcon: ({ color }) => (
            <Activity size={22} color={color} />
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
          tabBarIcon: ({ color }) => (
            <User size={22} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
