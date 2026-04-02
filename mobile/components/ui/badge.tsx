import { View } from "react-native";
import { cn } from "~/lib/utils";
import { Text } from "./text";

type Variant = "default" | "secondary" | "outline" | "destructive";

const variantStyles: Record<Variant, string> = {
  default: "bg-primary",
  secondary: "bg-secondary",
  outline: "border border-border bg-background",
  destructive: "bg-destructive",
};

const textStyles: Record<Variant, string> = {
  default: "text-primary-foreground",
  secondary: "text-secondary-foreground",
  outline: "text-foreground",
  destructive: "text-destructive-foreground",
};

interface BadgeProps {
  variant?: Variant;
  className?: string;
  children: string;
}

export function Badge({ variant = "secondary", className, children }: BadgeProps) {
  return (
    <View className={cn("rounded-md px-2.5 py-0.5", variantStyles[variant], className)}>
      <Text className={cn("text-xs font-medium", textStyles[variant])}>{children}</Text>
    </View>
  );
}
