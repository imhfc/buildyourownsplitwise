import { Pressable, View, type PressableProps, type ViewProps } from "react-native";
import { cn } from "~/lib/utils";

interface CardProps extends PressableProps {
  className?: string;
  children: React.ReactNode;
}

export function Card({ className, children, onPress, ...props }: CardProps) {
  if (onPress) {
    return (
      <Pressable
        className={cn(
          "rounded-2xl border border-border bg-card shadow-sm active:scale-[0.98]",
          className
        )}
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
        "rounded-2xl border border-border bg-card shadow-sm",
        className
      )}
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
  return <View className={cn("p-4 pb-2", className)} {...props} />;
}

export function CardContent({ className, ...props }: CardSectionProps) {
  return <View className={cn("p-4 pt-0", className)} {...props} />;
}

export function CardFooter({ className, ...props }: CardSectionProps) {
  return (
    <View
      className={cn("flex-row justify-end gap-2 p-4 pt-0", className)}
      {...props}
    />
  );
}
