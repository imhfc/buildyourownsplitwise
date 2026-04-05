import {
  Pressable,
  type PressableProps,
  ActivityIndicator,
} from "react-native";
import { cn } from "~/lib/utils";
import { Text } from "./text";

type Variant = "default" | "secondary" | "outline" | "destructive" | "ghost";
type Size = "default" | "sm" | "lg" | "icon";

const variantStyles: Record<Variant, string> = {
  default: "bg-primary active:opacity-90",
  secondary: "bg-secondary active:opacity-90",
  outline: "border border-input bg-background active:bg-accent",
  destructive: "bg-destructive active:opacity-90",
  ghost: "active:bg-accent",
};

const variantTextStyles: Record<Variant, string> = {
  default: "text-primary-foreground",
  secondary: "text-secondary-foreground",
  outline: "text-foreground",
  destructive: "text-destructive-foreground",
  ghost: "text-foreground",
};

const sizeStyles: Record<Size, string> = {
  default: "h-10 px-4",
  sm: "h-9 px-3",
  lg: "h-11 px-6",
  icon: "h-10 w-10",
};

const sizeTextStyles: Record<Size, string> = {
  default: "text-sm",
  sm: "text-sm",
  lg: "text-sm",
  icon: "text-sm",
};

interface ButtonProps extends PressableProps {
  variant?: Variant;
  size?: Size;
  className?: string;
  textClassName?: string;
  loading?: boolean;
  children: React.ReactNode;
}

export function Button({
  variant = "default",
  size = "default",
  className,
  textClassName,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      className={cn(
        "flex-row items-center justify-center rounded-lg",
        variantStyles[variant],
        sizeStyles[size],
        isDisabled && "opacity-50",
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === "default" || variant === "destructive" ? "#fff" : undefined}
          className="mr-2"
        />
      ) : null}
      {typeof children === "string" ? (
        <Text
          className={cn(
            "font-medium",
            variantTextStyles[variant],
            sizeTextStyles[size],
            textClassName
          )}
        >
          {children}
        </Text>
      ) : (
        children
      )}
    </Pressable>
  );
}
