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
    <View className={cn("flex-row rounded-lg bg-muted p-1", className)}>
      {tabs.map((tab) => {
        const isActive = tab.value === value;
        return (
          <Pressable
            key={tab.value}
            onPress={() => onValueChange(tab.value)}
            className={cn(
              "flex-1 items-center justify-center rounded-md py-2",
              isActive && "bg-background"
            )}
          >
            <Text
              className={cn(
                "text-sm font-medium",
                isActive ? "text-foreground" : "text-muted-foreground"
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
