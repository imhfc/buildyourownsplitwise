import { useCallback, useEffect } from "react";
import { Platform } from "react-native";
import { Tabs, useFocusEffect, usePathname } from "expo-router";
import { useTranslation } from "react-i18next";
import { UserPlus, SquaresFour, ClockCounterClockwise, UserCircle } from "phosphor-react-native";
import { useTheme, COLOR_SCHEMES } from "~/lib/theme";
import { useNotificationStore } from "~/stores/notification";
import { usePendingSettlementsStore } from "~/stores/pending-settlements";
import { useAuthStore } from "~/stores/auth";

export default function TabsLayout() {
  const { t } = useTranslation();
  const { isDark, colorScheme } = useTheme();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const fetchUnreadCount = useNotificationStore((s) => s.fetchUnreadCount);
  const pendingSettlementCount = usePendingSettlementsStore((s) => s.count);
  const fetchPendingSettlementCount = usePendingSettlementsStore((s) => s.fetchCount);

  const scheme = COLOR_SCHEMES.find((s) => s.id === colorScheme) ?? COLOR_SCHEMES[0];
  const activeTint = isDark ? scheme.preview.dark : scheme.preview.light;
  const inactiveTint = isDark ? "#A1A1AA" : "#71717A";

  // 每次 tab layout 獲得焦點時拉取未讀數量
  useFocusEffect(
    useCallback(() => {
      if (isAuthenticated) {
        fetchUnreadCount();
        fetchPendingSettlementCount();
      }
    }, [isAuthenticated, fetchUnreadCount, fetchPendingSettlementCount])
  );

  // 定期輪詢未讀數量（每 30 秒）
  useEffect(() => {
    if (!isAuthenticated) return;
    const interval = setInterval(() => {
      fetchUnreadCount();
      fetchPendingSettlementCount();
    }, 30_000);
    return () => clearInterval(interval);
  }, [isAuthenticated, fetchUnreadCount, fetchPendingSettlementCount]);

  const tabBarShadow = Platform.select({
    web: {
      boxShadow: "0 -1px 6px rgba(0,0,0,0.04)",
    } as any,
    default: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: -1 },
      shadowOpacity: 0.04,
      shadowRadius: 6,
      elevation: 3,
    },
  });

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: activeTint,
        tabBarInactiveTintColor: inactiveTint,
        tabBarStyle: {
          backgroundColor: isDark ? "#101318" : "#FFFFFF",
          borderTopWidth: 0,
          height: 52,
          paddingBottom: 4,
          paddingTop: 2,
          ...tabBarShadow,
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
          tabBarIcon: ({ color, focused }) => (
            <UserPlus size={22} color={color} weight={focused ? "fill" : "regular"} />
          ),
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: t("groups"),
          tabBarIcon: ({ color, focused }) => (
            <SquaresFour size={22} color={color} weight={focused ? "fill" : "regular"} />
          ),
          tabBarBadge: pendingSettlementCount > 0 ? pendingSettlementCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: "#F59E0B",
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
        name="activities"
        options={{
          title: t("activities"),
          tabBarIcon: ({ color, focused }) => (
            <ClockCounterClockwise size={22} color={color} weight={focused ? "fill" : "regular"} />
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
          tabBarIcon: ({ color, focused }) => (
            <UserCircle size={22} color={color} weight={focused ? "fill" : "regular"} />
          ),
        }}
      />
    </Tabs>
  );
}
