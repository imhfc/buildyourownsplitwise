import { TextInput, View, type TextInputProps } from "react-native";
import { cn } from "~/lib/utils";
import { Text } from "./text";

interface InputProps extends TextInputProps {
  className?: string;
  label?: string;
  error?: string;
  helper?: string;
}

export function Input({
  className,
  label,
  error,
  helper,
  ...props
}: InputProps) {
  return (
    <View className="gap-1.5">
      {label ? (
        <Text className="text-sm font-medium text-foreground">{label}</Text>
      ) : null}
      <TextInput
        className={cn(
          "h-12 rounded-xl border border-input bg-background px-4 text-base text-foreground",
          "focus:border-ring",
          error && "border-destructive",
          className
        )}
        placeholderTextColor="hsl(240 3.8% 46.1%)"
        {...props}
      />
      {error ? (
        <Text className="text-xs text-destructive">{error}</Text>
      ) : helper ? (
        <Text className="text-xs text-muted-foreground">{helper}</Text>
      ) : null}
    </View>
  );
}
