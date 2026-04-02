import { Pressable, View, Platform, type PressableProps, type ViewProps, type ViewStyle } from "react-native";
import { cn } from "~/lib/utils";
import { useTheme } from "~/lib/theme";

const lightShadow: ViewStyle = Platform.select({
  web: {
    boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
  } as any,
  default: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
}) ?? {};

const darkShadow: ViewStyle = Platform.select({
  web: {
    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)",
  } as any,
  default: {},
}) ?? {};

interface CardProps extends PressableProps {
  className?: string;
  children: React.ReactNode;
}

export function Card({ className, children, onPress, ...props }: CardProps) {
  const { isDark } = useTheme();
  const shadow = isDark ? darkShadow : lightShadow;
  const borderCls = isDark ? "border border-border" : "";

  if (onPress) {
    return (
      <Pressable
        className={cn(
          "rounded-xl bg-card",
          borderCls,
          className
        )}
        style={shadow}
        onPress={onPress}
        {...props}
      >
        {children}
      </Pressable>
    );
  }

  return (
    <View
      className={cn(
        "rounded-xl bg-card",
        borderCls,
        className
      )}
      style={shadow}
    >
      {children}
    </View>
  );
}

interface CardSectionProps extends ViewProps {
  className?: string;
  children: React.ReactNode;
}

export function CardHeader({ className, ...props }: CardSectionProps) {
  return <View className={cn("p-5 pb-2", className)} {...props} />;
}

export function CardContent({ className, ...props }: CardSectionProps) {
  return <View className={cn("p-5 pt-0", className)} {...props} />;
}

export function CardFooter({ className, ...props }: CardSectionProps) {
  return (
    <View
      className={cn("flex-row justify-end gap-2 p-5 pt-0", className)}
      {...props}
    />
  );
}
