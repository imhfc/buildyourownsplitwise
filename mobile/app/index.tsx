import { ActivityIndicator, View } from "react-native";

export default function Index() {
  // Auth redirect is handled by _layout.tsx useEffect
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <ActivityIndicator size="large" />
    </View>
  );
}
