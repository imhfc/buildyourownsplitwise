import { Pressable, View } from "react-native";
import { cn } from "~/lib/utils";
import { Text } from "./text";

interface Tab {
  value: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function SegmentedTabs({ tabs, value, onValueChange, className }: TabsProps) {
  return (
    <View className={cn("flex-row border-b border-border", className)}>
      {tabs.map((tab) => {
        const isActive = tab.value === value;
        return (
          <Pressable
            key={tab.value}
            onPress={() => onValueChange(tab.value)}
            className={cn(
              "flex-1 items-center justify-center pb-2.5 pt-1",
              isActive && "border-b border-primary"
            )}
          >
            <Text
              className={cn(
                "text-sm",
                isActive
                  ? "text-foreground font-semibold"
                  : "text-muted-foreground font-medium"
              )}
            >
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
