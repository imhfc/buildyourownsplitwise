import { Pressable, type PressableProps } from "react-native";
import { cn } from "~/lib/utils";
import { Plus } from "lucide-react-native";

interface FABProps extends PressableProps {
  className?: string;
  icon?: React.ReactNode;
}

export function FAB({ className, icon, ...props }: FABProps) {
  return (
    <Pressable
      className={cn(
        "absolute bottom-6 right-5 h-14 w-14 items-center justify-center rounded-xl bg-primary shadow-md active:scale-[0.97]",
        className
      )}
      {...props}
    >
      {icon ?? <Plus size={24} color="#fff" />}
    </Pressable>
  );
}
