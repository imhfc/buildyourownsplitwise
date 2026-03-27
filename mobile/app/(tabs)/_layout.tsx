import { Tabs } from "expo-router";
import { useTranslation } from "react-i18next";
import { Users, Settings } from "lucide-react-native";
import { useTheme } from "~/lib/theme";

export default function TabsLayout() {
  const { t } = useTranslation();
  const { isDark } = useTheme();

  const activeTint = isDark ? "#60A5FA" : "#2563EB";
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
        name="index"
        options={{
          title: t("groups"),
          tabBarIcon: ({ color, size }) => (
            <Users size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t("settings"),
          tabBarIcon: ({ color, size }) => (
            <Settings size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
