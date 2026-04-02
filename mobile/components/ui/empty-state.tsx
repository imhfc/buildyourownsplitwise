import { View } from "react-native";
import { cn } from "~/lib/utils";
import { Text, Muted } from "./text";
import { Button } from "./button";
import type { IconProps } from "phosphor-react-native";

interface EmptyStateProps {
  icon: React.ComponentType<IconProps>;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <View className={cn("items-center justify-center py-16 px-8", className)}>
      <Icon size={48} color="hsl(240 3.8% 46.1%)" weight="regular" />
      <Text className="mt-4 text-lg font-medium text-center">{title}</Text>
      {description ? (
        <Muted className="mt-1 text-center">{description}</Muted>
      ) : null}
      {actionLabel && onAction ? (
        <Button onPress={onAction} className="mt-6">
          {actionLabel}
        </Button>
      ) : null}
    </View>
  );
}
