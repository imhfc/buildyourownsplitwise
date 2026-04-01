import { View, Image } from "react-native";
import { cn } from "~/lib/utils";
import { Text } from "./text";
import { getAvatarColor, getInitials } from "~/lib/constants";

type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";

const sizeStyles: Record<AvatarSize, string> = {
  xs: "h-6 w-6",
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-14 w-14",
  xl: "h-20 w-20",
};

const textSizeStyles: Record<AvatarSize, string> = {
  xs: "text-[10px]",
  sm: "text-xs",
  md: "text-sm",
  lg: "text-xl",
  xl: "text-2xl",
};

interface AvatarProps {
  name: string;
  avatarUrl?: string | null;
  index?: number;
  size?: AvatarSize;
  className?: string;
}

const imageSizeMap: Record<AvatarSize, number> = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 56,
  xl: 80,
};

export function Avatar({
  name,
  avatarUrl,
  index = 0,
  size = "md",
  className,
}: AvatarProps) {
  const color = getAvatarColor(index);
  const initials = getInitials(name);
  const px = imageSizeMap[size];

  if (avatarUrl) {
    return (
      <Image
        source={{ uri: avatarUrl }}
        style={{ width: px, height: px, borderRadius: px / 2 }}
        className={className}
      />
    );
  }

  return (
    <View
      className={cn(
        "items-center justify-center rounded-full",
        sizeStyles[size],
        className
      )}
      style={{ backgroundColor: color }}
    >
      <Text
        className={cn("font-semibold text-white", textSizeStyles[size])}
      >
        {initials}
      </Text>
    </View>
  );
}

interface AvatarStackProps {
  names: string[];
  size?: AvatarSize;
  max?: number;
  className?: string;
}

export function AvatarStack({
  names,
  size = "sm",
  max = 3,
  className,
}: AvatarStackProps) {
  const visible = names.slice(0, max);
  const remaining = names.length - max;

  return (
    <View className={cn("flex-row", className)}>
      {visible.map((name, i) => (
        <View
          key={i}
          className={cn("border-2 border-background rounded-full", i > 0 && "-ml-2")}
        >
          <Avatar name={name} index={i} size={size} />
        </View>
      ))}
      {remaining > 0 ? (
        <View
          className={cn(
            "items-center justify-center rounded-full border-2 border-background bg-muted -ml-2",
            sizeStyles[size]
          )}
        >
          <Text className={cn("font-semibold text-muted-foreground", textSizeStyles[size])}>
            +{remaining}
          </Text>
        </View>
      ) : null}
    </View>
  );
}
