import { Text as RNText, type TextProps } from "react-native";
import { cn } from "~/lib/utils";

interface Props extends TextProps {
  className?: string;
}

export function Text({ className, ...props }: Props) {
  return (
    <RNText
      className={cn("text-base text-foreground", className)}
      {...props}
    />
  );
}

export function H1({ className, ...props }: Props) {
  return (
    <RNText
      className={cn("text-3xl font-bold tracking-tight text-foreground", className)}
      {...props}
    />
  );
}

export function H2({ className, ...props }: Props) {
  return (
    <RNText
      className={cn("text-2xl font-semibold tracking-tight text-foreground", className)}
      {...props}
    />
  );
}

export function H3({ className, ...props }: Props) {
  return (
    <RNText
      className={cn("text-lg font-semibold tracking-tight text-foreground", className)}
      {...props}
    />
  );
}

export function Muted({ className, ...props }: Props) {
  return (
    <RNText
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}
