import { Pressable, Text, type PressableProps } from "react-native";
import { cn } from "~/lib/utils";
import { Plus } from "phosphor-react-native";

interface FABProps extends PressableProps {
  className?: string;
  icon?: React.ReactNode;
  label?: string;
}

export function FAB({ className, icon, label, ...props }: FABProps) {
  return (
    <Pressable
      className={cn(
        "absolute bottom-6 right-5 flex-row items-center justify-center bg-primary shadow-md active:scale-[0.97]",
        label ? "h-12 gap-1.5 rounded-full px-4" : "h-14 w-14 rounded-xl",
        className
      )}
      {...props}
    >
      {icon ?? <Plus size={label ? 20 : 24} color="#fff" />}
      {label ? (
        <Text className="text-sm font-semibold text-primary-foreground">{label}</Text>
      ) : null}
    </Pressable>
  );
}
