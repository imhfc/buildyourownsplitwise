import React from "react";
import { View } from "react-native";
import Svg, { Rect, Path, Line } from "react-native-svg";
import { useTheme, COLOR_SCHEMES } from "~/lib/theme";

interface LogoProps {
  size?: number;
}

export function Logo({ size = 96 }: LogoProps) {
  const { colorScheme, isDark } = useTheme();
  const scheme =
    COLOR_SCHEMES.find((s) => s.id === colorScheme) ?? COLOR_SCHEMES[0];
  const color = isDark ? scheme.preview.dark : scheme.preview.light;

  return (
    <View style={{ alignItems: "center" }}>
      <Svg width={size} height={size} viewBox="0 0 100 100">
        {/* Rounded square background */}
        <Rect x="2" y="2" width="96" height="96" rx="22" fill={color} />

        {/* Left receipt half — zigzag right edge */}
        <Path
          d="M 20 19 C 20 16.5 22 15 24.5 15 L 46 15 L 50 20 L 46 25 L 50 30 L 46 35 L 50 40 L 46 45 L 50 50 L 46 55 L 50 60 L 46 65 L 50 70 L 46 75 L 50 80 L 46 85 L 24.5 85 C 22 85 20 83.5 20 81 Z"
          fill="white"
          opacity={0.95}
        />

        {/* Right receipt half — zigzag left edge */}
        <Path
          d="M 54 15 L 75.5 15 C 78 15 80 16.5 80 19 L 80 81 C 80 83.5 78 85 75.5 85 L 54 85 L 50 80 L 54 75 L 50 70 L 54 65 L 50 60 L 54 55 L 50 50 L 54 45 L 50 40 L 54 35 L 50 30 L 54 25 L 50 20 Z"
          fill="white"
          opacity={0.8}
        />

        {/* Left receipt — line items */}
        <Line x1="25" y1="28" x2="42" y2="28" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />
        <Line x1="25" y1="36" x2="37" y2="36" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />
        <Line x1="25" y1="44" x2="42" y2="44" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />
        <Line x1="25" y1="52" x2="35" y2="52" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />

        {/* Left receipt — total line */}
        <Line x1="25" y1="70" x2="42" y2="70" stroke={color} strokeWidth="3" strokeLinecap="round" opacity={0.55} />

        {/* Right receipt — line items */}
        <Line x1="58" y1="28" x2="76" y2="28" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />
        <Line x1="58" y1="36" x2="71" y2="36" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />
        <Line x1="58" y1="44" x2="76" y2="44" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />
        <Line x1="58" y1="52" x2="69" y2="52" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity={0.3} />

        {/* Right receipt — total line */}
        <Line x1="58" y1="70" x2="76" y2="70" stroke={color} strokeWidth="3" strokeLinecap="round" opacity={0.55} />
      </Svg>
    </View>
  );
}
