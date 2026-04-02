import { Pressable, View, Platform, type ViewStyle } from "react-native";
import { cn } from "~/lib/utils";
import { Text } from "./text";

const activeTabShadow: ViewStyle = Platform.select({
  web: {
    boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
  } as any,
  default: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
}) ?? {};

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
    <View className={cn("flex-row rounded-lg bg-border p-1", className)}>
      {tabs.map((tab) => {
        const isActive = tab.value === value;
        return (
          <Pressable
            key={tab.value}
            onPress={() => onValueChange(tab.value)}
            className={cn(
              "flex-1 items-center justify-center rounded-md py-2",
              isActive && "bg-card"
            )}
            style={isActive ? activeTabShadow : undefined}
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
