import React from "react";
import { Image, View } from "react-native";
import { useTheme } from "~/lib/theme";

interface LogoProps {
  size?: number;
}

export function Logo({ size = 96 }: LogoProps) {
  const { isDark } = useTheme();

  return (
    <View style={{ alignItems: "center" }}>
      <Image
        source={require("../assets/logo-transparent.png")}
        style={{
          width: size,
          height: size,
          tintColor: isDark ? "#E2E8F0" : undefined,
        }}
        resizeMode="contain"
      />
    </View>
  );
}
