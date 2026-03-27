import { PaperProvider, MD3LightTheme } from "react-native-paper";
import { Stack } from "expo-router";
import "../i18n";

const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: "#2563EB",
    secondary: "#7C3AED",
    tertiary: "#059669",
  },
};

export default function RootLayout() {
  return (
    <PaperProvider theme={theme}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen
          name="group/[id]"
          options={{ headerShown: true, title: "" }}
        />
      </Stack>
    </PaperProvider>
  );
}
