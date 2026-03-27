export const AVATAR_COLORS = [
  "#2563EB",
  "#7C3AED",
  "#059669",
  "#DC2626",
  "#D97706",
  "#0891B2",
  "#DB2777",
  "#4F46E5",
  "#65A30D",
  "#9333EA",
] as const;

export function getAvatarColor(index: number): string {
  return AVATAR_COLORS[index % AVATAR_COLORS.length];
}

export function getInitials(name: string): string {
  if (!name) return "?";
  // For CJK characters, take the first character
  if (/[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]/.test(name)) {
    return name.charAt(0);
  }
  // For Latin characters, take first two letters uppercase
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}
