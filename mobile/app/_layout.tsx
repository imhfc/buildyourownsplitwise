import "../global.css";
import "../i18n";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { ThemeProvider, useTheme } from "~/lib/theme";

function InnerLayout() {
  const { isDark } = useTheme();

  return (
    <View className={isDark ? "dark flex-1" : "flex-1"}>
      <View className="flex-1 bg-background">
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: "transparent" },
          }}
        >
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen
            name="group/[id]"
            options={{
              headerShown: true,
              title: "",
              headerStyle: { backgroundColor: "transparent" },
              headerTintColor: isDark ? "#FAFAFA" : "#09090B",
              headerShadowVisible: false,
            }}
          />
        </Stack>
        <StatusBar style={isDark ? "light" : "dark"} />
      </View>
    </View>
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
