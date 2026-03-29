import { Tabs } from "expo-router";
import { useTranslation } from "react-i18next";
import { UserPlus, Users, Activity, User } from "lucide-react-native";
import { useTheme, COLOR_SCHEMES } from "~/lib/theme";

export default function TabsLayout() {
  const { t } = useTranslation();
  const { isDark, colorScheme } = useTheme();

  const scheme = COLOR_SCHEMES.find((s) => s.id === colorScheme) ?? COLOR_SCHEMES[0];
  const activeTint = isDark ? scheme.preview.dark : scheme.preview.light;
  const inactiveTint = isDark ? "#A1A1AA" : "#71717A";

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: activeTint,
        tabBarInactiveTintColor: inactiveTint,
        tabBarStyle: {
          backgroundColor: isDark ? "#09090B" : "#FFFFFF",
          borderTopColor: isDark ? "#27272A" : "#E4E4E7",
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
