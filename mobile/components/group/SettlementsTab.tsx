import { View, ScrollView, RefreshControl, ActivityIndicator } from "react-native";
import { useTranslation } from "react-i18next";
import { ArrowsLeftRight, Megaphone } from "phosphor-react-native";
import { Card, CardContent } from "~/components/ui/card";
import { Text } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { EmptyState } from "~/components/ui/empty-state";
import type { Suggestion, PendingSettlement } from "./types";

interface SettlementsTabProps {
  suggestions: Suggestion[];
  pendingSettlements: PendingSettlement[];
  userId: string;
  groupId: string;
  groupCurrency: string;
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  listHeader: React.ReactNode;
  settleSuccessMsg: string;
  batchReminding: boolean;
  onSettleUp: (item: Suggestion) => void;
  onUnifiedSettle: (personId: string, name: string, items: Suggestion[], currency: string) => void;
  onRemind: (item: Suggestion) => Promise<void>;
  onBatchRemind: (items: Suggestion[]) => Promise<void>;
  onForgive: (item: Suggestion) => void;
  hasPendingFor: (fromId: string, toId: string) => boolean;
}

export function SettlementsTab({
  suggestions,
  pendingSettlements,
  userId,
  groupCurrency,
  loading,
  refreshing,
  onRefresh,
  listHeader,
  settleSuccessMsg,
  batchReminding,
  onSettleUp,
  onUnifiedSettle,
  onRemind,
  onBatchRemind,
  onForgive,
  hasPendingFor,
}: SettlementsTabProps) {
  const { t } = useTranslation();

  const mySuggestions = suggestions.filter((s) => s.from_user_id === userId || s.to_user_id === userId);
  const owedToMe = mySuggestions.filter((s) => s.to_user_id === userId);
  const iOwe = mySuggestions.filter((s) => s.from_user_id === userId);

  if (loading) {
    return (
      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 100 }}>
        {listHeader}
        <View className="items-center justify-center py-20">
          <ActivityIndicator size="large" />
        </View>
      </ScrollView>
    );
  }

  const isEmpty = mySuggestions.length === 0 && pendingSettlements.length === 0;

  return (
    <ScrollView
      contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 100 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {listHeader}

      {settleSuccessMsg ? (
        <View className="bg-primary/10 rounded-lg px-4 py-3 mb-4">
          <Text className="text-sm text-primary font-medium">{settleSuccessMsg}</Text>
        </View>
      ) : null}

      {isEmpty ? (
        <EmptyState
          icon={ArrowsLeftRight}
          title={t("balanced")}
          description={t("all_balanced_hint")}
        />
      ) : (
        <View className="gap-4">
          {/* Pending settlements */}
          {pendingSettlements.length > 0 && (
            <Card>
              <CardContent className="p-3.5 gap-2">
                <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {t("pending_settlements")}
                </Text>
                {pendingSettlements.map((s) => (
                  <View key={s.id} className="flex-row items-center justify-between py-1">
                    <Text className="text-sm flex-1">
                      {s.from_user_name} → {s.to_user_name}
                    </Text>
                    <Text className="text-sm font-medium text-warning">
                      {s.currency} {s.amount.toLocaleString()}
                    </Text>
                  </View>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Section: Others owe me */}
          {owedToMe.length > 0 && (
            <Card>
              <CardContent className="p-3.5 gap-2.5">
                <View className="flex-row items-center justify-between">
                  <Text className="text-xs font-medium text-income uppercase tracking-wider">
                    {t("owed_to_you")}
                  </Text>
                  {owedToMe.length > 1 && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={batchReminding}
                      onPress={() => onBatchRemind(owedToMe)}
                    >
                      <View className="flex-row items-center gap-1">
                        <Megaphone size={14} color="hsl(var(--primary))" />
                        <Text className="text-xs">{t("batch_remind_all")}</Text>
                      </View>
                    </Button>
                  )}
                </View>
                {owedToMe.map((item) => {
                  const alreadyPending = hasPendingFor(item.from_user_id, item.to_user_id);
                  return (
                    <View key={`${item.from_user_id}-${item.to_user_id}-${item.currency}`} className="gap-2">
                      <View className="flex-row items-center justify-between">
                        <Text className="text-sm flex-1">
                          {t("owes_you", { name: item.from_user_name })}
                        </Text>
                        <Text className="text-sm font-semibold tabular-nums text-income">
                          {item.currency} {parseFloat(item.amount).toLocaleString()}
                        </Text>
                      </View>
                      {alreadyPending && (
                        <Text className="text-xs text-warning">{t("settlement_pending_hint")}</Text>
                      )}
                      <View className="flex-row gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onPress={() => onRemind(item)}
                          className="flex-1"
                        >
                          {t("remind")}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onPress={() => onForgive(item)}
                          className="flex-1"
                        >
                          {t("forgive_debt")}
                        </Button>
                      </View>
                    </View>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {/* Section: I owe others (grouped by person) */}
          {iOwe.length > 0 && (() => {
            const grouped = new Map<string, { name: string; items: Suggestion[] }>();
            for (const item of iOwe) {
              if (!grouped.has(item.to_user_id)) {
                grouped.set(item.to_user_id, { name: item.to_user_name, items: [] });
              }
              grouped.get(item.to_user_id)!.items.push(item);
            }
            return (
              <Card>
                <CardContent className="p-3.5 gap-2.5">
                  <Text className="text-xs font-medium text-destructive uppercase tracking-wider">
                    {t("you_owe")}
                  </Text>
                  {Array.from(grouped).map(([personId, { name, items }]) => {
                    const alreadyPending = hasPendingFor(items[0].from_user_id, personId);
                    const canSettle = items[0].from_user_id === userId;
                    const hasMultipleCurrencies = items.length > 1;
                    return (
                      <View key={personId} className="gap-2">
                        <View className="flex-row items-center justify-between">
                          <Text className="text-sm font-medium flex-1">
                            {t("you_owe_person", { name })}
                          </Text>
                          {canSettle && hasMultipleCurrencies && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={alreadyPending}
                              onPress={() => onUnifiedSettle(personId, name, items, groupCurrency)}
                            >
                              {t("unified_settle")}
                            </Button>
                          )}
                        </View>
                        {alreadyPending && (
                          <Text className="text-xs text-warning pl-3">{t("settlement_pending_hint")}</Text>
                        )}
                        {items.map((item) => (
                          <View key={`${item.from_user_id}-${item.to_user_id}-${item.currency}`} className="flex-row items-center justify-between pl-3">
                            <Text className="text-sm font-semibold tabular-nums text-destructive flex-1">
                              {item.currency} {parseFloat(item.amount).toLocaleString()}
                            </Text>
                            {canSettle && (
                              <Button
                                size="sm"
                                disabled={alreadyPending}
                                onPress={() => onSettleUp(item)}
                              >
                                {alreadyPending ? t("settlement_pending_hint") : t("settle_up")}
                              </Button>
                            )}
                          </View>
                        ))}
                      </View>
                    );
                  })}
                </CardContent>
              </Card>
            );
          })()}
        </View>
      )}
    </ScrollView>
  );
}
