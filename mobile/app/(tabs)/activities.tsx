import { useCallback, useRef, useState } from "react";
import { View, FlatList, RefreshControl, ActivityIndicator } from "react-native";
import { useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { Receipt, ArrowsLeftRight, ClockCounterClockwise } from "phosphor-react-native";
import { Text, Muted } from "~/components/ui/text";
import { EmptyState } from "~/components/ui/empty-state";
import { activitiesAPI } from "../../services/api";
import { useNotificationStore } from "~/stores/notification";
import { useTheme } from "~/lib/theme";

interface ActivityItem {
  type: "expense_added" | "settlement_created";
  group_id: string;
  group_name: string;
  actor_name: string;
  description: string | null;
  to_name: string | null;
  amount: string;
  currency: string;
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

function ActivityRow({ item }: { item: ActivityItem }) {
  const { t } = useTranslation();
  const { isDark } = useTheme();
  const isExpense = item.type === "expense_added";
  const iconColor = isExpense ? "#22c55e" : "#3b82f6";
  const iconBg = isExpense
    ? (isDark ? "rgba(34,197,94,0.15)" : "#dcfce7")
    : (isDark ? "rgba(59,130,246,0.15)" : "#dbeafe");

  const description = isExpense
    ? `${item.actor_name} ${t("expense_added")}「${item.description}」${t("in_group")} ${item.group_name}`
    : `${item.actor_name} ${t("settlement_created")}，${t("in_group")} ${item.group_name} ${t("to")} ${item.to_name}`;

  return (
    <View className="flex-row items-start px-5 py-3 gap-3">
      <View
        className="mt-0.5 h-9 w-9 rounded-full items-center justify-center"
        style={{ backgroundColor: iconBg }}
      >
        {isExpense
          ? <Receipt size={18} color={iconColor} weight="regular" />
          : <ArrowsLeftRight size={18} color={iconColor} weight="regular" />
        }
      </View>
      <View className="flex-1">
        <Text className="text-sm leading-5">{description}</Text>
        <View className="flex-row items-center mt-1 gap-2">
          <Text className="text-sm font-semibold">
            {item.currency} {Number(item.amount).toLocaleString()}
          </Text>
          <Muted className="text-xs">{formatRelativeTime(item.timestamp)}</Muted>
        </View>
      </View>
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
      contentContainerStyle={items.length === 0 ? { flex: 1 } : undefined}
      className="flex-1 bg-background"
    />
  );
}
