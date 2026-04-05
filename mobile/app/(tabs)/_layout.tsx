import { useCallback, useEffect } from "react";
import { Image, Platform, View } from "react-native";
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
  const inactiveTint = isDark ? "#52525B" : "#A1A1AA";

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
          backgroundColor: isDark ? "#0A0C0F" : "#FFFFFF",
          borderTopWidth: 1,
          borderTopColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)",
          height: 50,
          paddingBottom: 4,
          paddingTop: 4,
        },
        tabBarIconStyle: {
          marginBottom: -2,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "500",
          marginTop: -2,
          letterSpacing: 0.2,
        },
        headerStyle: {
          backgroundColor: isDark ? "#0A0C0F" : "#FFFFFF",
        },
        headerTintColor: isDark ? "#FAFAFA" : "#18181B",
        headerShadowVisible: false,
      }}
    >
      <Tabs.Screen
        name="friends"
        options={{
          title: t("friends"),
          tabBarIcon: ({ color, focused }) => (
            <UserPlus size={20} color={color} weight={focused ? "fill" : "regular"} />
          ),
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: t("groups"),
          headerTitle: () => (
            <Image
              source={require("../../assets/logo-transparent.png")}
              style={{
                width: 28,
                height: 28,
                tintColor: isDark ? "#E2E8F0" : undefined,
              }}
              resizeMode="contain"
            />
          ),
          tabBarIcon: ({ color, focused }) => (
            <SquaresFour size={20} color={color} weight={focused ? "fill" : "regular"} />
          ),
          tabBarBadge: pendingSettlementCount > 0 ? pendingSettlementCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: isDark ? "#52525B" : "#18181B",
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
            <ClockCounterClockwise size={20} color={color} weight={focused ? "fill" : "regular"} />
          ),
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: isDark ? "#52525B" : "#18181B",
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
            <UserCircle size={20} color={color} weight={focused ? "fill" : "regular"} />
          ),
        }}
      />
    </Tabs>
  );
}
