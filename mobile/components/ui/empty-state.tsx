import { View } from "react-native";
import { cn } from "~/lib/utils";
import { Text, Muted } from "./text";
import { Button } from "./button";
import { Logo } from "~/components/Logo";
import type { IconProps } from "phosphor-react-native";

interface EmptyStateProps {
  icon?: React.ComponentType<IconProps>;
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
      <View className="opacity-20 mb-4">
        <Logo size={56} />
      </View>
      {Icon ? (
        <Icon size={32} color="hsl(215 16% 47%)" weight="light" />
      ) : null}
      <Text className="mt-3 text-sm font-medium text-center">{title}</Text>
      {description ? (
        <Muted className="mt-1 text-center text-xs">{description}</Muted>
      ) : null}
      {actionLabel && onAction ? (
        <Button onPress={onAction} className="mt-5">
          {actionLabel}
        </Button>
      ) : null}
    </View>
  );
}
