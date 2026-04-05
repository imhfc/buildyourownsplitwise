import { useCallback, useEffect, useRef, useState } from "react";
import { View, FlatList, RefreshControl, ActivityIndicator, Pressable } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { Receipt, ArrowsLeftRight, ClockCounterClockwise, UserPlus, UserMinus, BellRinging, EnvelopeSimple, PencilSimple, Trash, CaretRight } from "phosphor-react-native";
import { Text, Muted } from "~/components/ui/text";
import { EmptyState } from "~/components/ui/empty-state";
import { activitiesAPI } from "../../services/api";
import { useNotificationStore } from "~/stores/notification";
import { useTheme } from "~/lib/theme";
import { Logo } from "~/components/Logo";
import { addNotificationReceivedCallback } from "~/lib/notifications";

type ActivityType =
  | "expense_added"
  | "expense_updated"
  | "expense_adjusted"
  | "expense_deleted"
  | "settlement_created"
  | "settlement_confirmed"
  | "settlement_rejected"
  | "settlement_forgiven"
  | "member_added"
  | "member_removed"
  | "reminder_sent"
  | "email_invitation_sent"
  | "email_invitation_cancelled";

interface ActivityItem {
  type: ActivityType;
  group_id: string;
  group_name: string;
  actor_name: string;
  description: string | null;
  to_name: string | null;
  amount: string | null;
  currency: string | null;
  timestamp: string;
}

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d`;
  const months = Math.floor(days / 30);
  return `${months}mo`;
}

function getActivityStyle(type: ActivityType, isDark: boolean) {
  switch (type) {
    case "expense_added":
    case "expense_updated":
    case "expense_adjusted":
      return { color: "#22c55e", bg: isDark ? "rgba(34,197,94,0.15)" : "#dcfce7" };
    case "expense_deleted":
      return { color: "#ef4444", bg: isDark ? "rgba(239,68,68,0.15)" : "#fee2e2" };
    case "settlement_created":
    case "settlement_confirmed":
    case "settlement_rejected":
    case "settlement_forgiven":
      return { color: "#3b82f6", bg: isDark ? "rgba(59,130,246,0.15)" : "#dbeafe" };
    case "member_added":
    case "member_removed":
      return { color: "#a855f7", bg: isDark ? "rgba(168,85,247,0.15)" : "#f3e8ff" };
    case "reminder_sent":
      return { color: "#f59e0b", bg: isDark ? "rgba(245,158,11,0.15)" : "#fef3c7" };
    case "email_invitation_sent":
    case "email_invitation_cancelled":
      return { color: "#6366f1", bg: isDark ? "rgba(99,102,241,0.15)" : "#e0e7ff" };
  }
}

function ActivityIcon({ type, color }: { type: ActivityType; color: string }) {
  const props = { size: 18, color, weight: "regular" as const };
  switch (type) {
    case "expense_added": return <Receipt {...props} />;
    case "expense_updated": return <PencilSimple {...props} />;
    case "expense_adjusted": return <PencilSimple {...props} />;
    case "expense_deleted": return <Trash {...props} />;
    case "settlement_created":
    case "settlement_confirmed":
    case "settlement_rejected":
    case "settlement_forgiven":
      return <ArrowsLeftRight {...props} />;
    case "member_added": return <UserPlus {...props} />;
    case "member_removed": return <UserMinus {...props} />;
    case "reminder_sent": return <BellRinging {...props} />;
    case "email_invitation_sent":
    case "email_invitation_cancelled":
      return <EnvelopeSimple {...props} />;
  }
}

function buildDescription(item: ActivityItem, t: (key: string) => string): string {
  const action = t(item.type);
  switch (item.type) {
    case "expense_added":
    case "expense_updated":
    case "expense_adjusted":
    case "expense_deleted":
      return `${item.actor_name} ${action}${item.description ? `「${item.description}」` : ""}${t("in_group")} ${item.group_name}`;
    case "settlement_created":
      return `${item.actor_name} ${action}，${t("in_group")} ${item.group_name} ${t("to")} ${item.to_name}`;
    case "settlement_confirmed":
    case "settlement_rejected":
      return `${item.actor_name} ${action}，${t("in_group")} ${item.group_name}`;
    case "settlement_forgiven":
      return `${item.actor_name} ${action}，${t("in_group")} ${item.group_name} ${t("to")} ${item.to_name}`;
    case "member_added":
    case "member_removed":
      return `${item.to_name ?? item.actor_name} ${action} ${item.group_name}`;
    case "reminder_sent":
      return `${item.actor_name} ${action}，${t("in_group")} ${item.group_name}`;
    case "email_invitation_sent":
    case "email_invitation_cancelled":
      return `${item.actor_name} ${action}，${t("in_group")} ${item.group_name}`;
  }
}

const NAVIGABLE_TYPES: Set<ActivityType> = new Set([
  "reminder_sent",
  "settlement_created",
  "settlement_confirmed",
  "settlement_rejected",
  "settlement_forgiven",
  "expense_added",
  "expense_updated",
  "expense_adjusted",
  "expense_deleted",
]);

function ActivityRow({ item }: { item: ActivityItem }) {
  const { t } = useTranslation();
  const { isDark } = useTheme();
  const router = useRouter();
  const style = getActivityStyle(item.type, isDark);
  const description = buildDescription(item, t);
  const hasAmount = item.amount != null && item.currency != null;
  const canNavigate = NAVIGABLE_TYPES.has(item.type);

  const handlePress = () => {
    if (canNavigate) {
      router.push(`/group/${item.group_id}`);
    }
  };

  const content = (
    <>
      <View
        className="mt-0.5 h-9 w-9 rounded-full items-center justify-center"
        style={{ backgroundColor: style.bg }}
      >
        <ActivityIcon type={item.type} color={style.color} />
      </View>
      <View className="flex-1">
        <Text className="text-sm leading-5">{description}</Text>
        <View className="flex-row items-center mt-1 gap-2">
          {hasAmount && (
            <Text className="text-sm font-semibold tabular-nums">
              {item.currency} {Number(item.amount).toLocaleString()}
            </Text>
          )}
          <Muted className="text-xs">{formatRelativeTime(item.timestamp)}</Muted>
        </View>
      </View>
      {canNavigate && (
        <View className="justify-center">
          <CaretRight size={16} color={isDark ? "#737373" : "#A3A3A3"} />
        </View>
      )}
    </>
  );

  if (canNavigate) {
    return (
      <Pressable
        className="flex-row items-start px-5 py-3 gap-3 active:opacity-70"
        onPress={handlePress}
      >
        {content}
      </Pressable>
    );
  }

  return (
    <View className="flex-row items-start px-5 py-3 gap-3">
      {content}
    </View>
  );
}

export default function ActivitiesScreen() {
  const { t } = useTranslation();
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasFetched = useRef(false);
  const markAsRead = useNotificationStore((s) => s.markAsRead);

  const fetchActivities = useCallback(async () => {
    const isFirstLoad = !hasFetched.current;
    if (isFirstLoad) setLoading(true);
    try {
      const res = await activitiesAPI.list();
      setItems(res.data);
      setError(null);
      hasFetched.current = true;
    } catch (err) {
      console.error("[activities] fetch failed:", err);
      setError(t("load_activities_failed"));
    } finally {
      if (isFirstLoad) setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchActivities();
      // 進入活動頁面時標記已讀
      markAsRead();
    }, [fetchActivities, markAsRead])
  );

  // 收到推播時即時刷新活動列表
  useEffect(() => {
    return addNotificationReceivedCallback(() => {
      fetchActivities();
      markAsRead();
    });
  }, [fetchActivities, markAsRead]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchActivities();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(_, idx) => String(idx)}
      renderItem={({ item }) => <ActivityRow item={item} />}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      ListEmptyComponent={
        error ? (
          <View className="flex-1 items-center justify-center px-6">
            <Text className="text-destructive text-center">{error}</Text>
          </View>
        ) : (
          <EmptyState
            icon={ClockCounterClockwise}
            title={t("no_activities_hint")}
          />
        )
      }
      ListFooterComponent={
        items.length > 0 ? (
          <View className="items-center pb-8 pt-6 opacity-30">
            <Logo size={32} />
          </View>
        ) : null
      }
      contentContainerStyle={items.length === 0 ? { flex: 1 } : undefined}
      className="flex-1 bg-background"
    />
  );
}
