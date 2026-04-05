import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { View, RefreshControl, Modal, Pressable, KeyboardAvoidingView, Platform, Animated, ActivityIndicator } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { UsersThree, X, Trash, SignOut, DotsSixVertical, CaretDown, CaretRight, EnvelopeSimple, Check, CurrencyCircleDollar } from "phosphor-react-native";
import { Swipeable } from "react-native-gesture-handler";
import DraggableFlatList, { ScaleDecorator, RenderItemParams } from "react-native-draggable-flatlist";
import { groupsAPI, inviteAPI, settlementsAPI, balancesAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { usePendingSettlementsStore } from "../../stores/pending-settlements";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { CurrencyPicker } from "~/components/ui/currency-picker";
import { useThemeClassName, useTheme } from "~/lib/theme";
import { addNotificationReceivedCallback } from "~/lib/notifications";

interface SimplifiedDebt {
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  amount: number;
  currency: string;
}

interface GroupItem {
  id: string;
  name: string;
  description: string | null;
  default_currency: string;
  member_count: number;
  created_at: string;
  created_by: string;
  my_role: string;
  sort_order: number;
  is_settled: boolean;
  unsettled_debts: SimplifiedDebt[];
}

interface CurrencyTotal {
  currency: string;
  owed_to_you: string;
  you_owe: string;
  net_balance: string;
}

export default function GroupsScreen() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const themeClass = useThemeClassName();
  const { isDark } = useTheme();
  const iconColor = isDark ? "#A1A1AA" : "#71717A";
  const syncBadgeCount = usePendingSettlementsStore((s) => s.fetchCount);
  const [groups, setGroups] = useState<GroupItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const hasFetched = useRef(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCurrency, setNewCurrency] = useState("TWD");
  const [creating, setCreating] = useState(false);
  const swipeableRefs = useRef<Map<string, Swipeable>>(new Map());
  const [confirmTarget, setConfirmTarget] = useState<{ item: GroupItem; action: "delete" | "leave" } | null>(null);
  const [settledExpanded, setSettledExpanded] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [overallTotals, setOverallTotals] = useState<CurrencyTotal[]>([]);

  // Pending email invitations
  interface PendingInvitation {
    id: string;
    group_id: string;
    group_name: string;
    group_description: string | null;
    inviter_name: string;
    member_count: number;
    created_at: string;
    expires_at: string;
  }
  const [pendingInvitations, setPendingInvitations] = useState<PendingInvitation[]>([]);
  const [respondingId, setRespondingId] = useState<string | null>(null);

  // Pending settlements
  interface PendingSettlement {
    id: string;
    group_id: string;
    group_name: string | null;
    from_user: string;
    from_user_name: string;
    to_user: string;
    to_user_name: string;
    amount: string;
    currency: string;
    status: string;
    settled_at: string;
    original_currency: string | null;
    original_amount: string | null;
    locked_rate: string | null;
  }
  const [pendingSettlements, setPendingSettlements] = useState<PendingSettlement[]>([]);
  const [respondingSettlementId, setRespondingSettlementId] = useState<string | null>(null);

  const fetchPendingSettlements = useCallback(async () => {
    try {
      const res = await settlementsAPI.pending();
      setPendingSettlements(res.data);
      syncBadgeCount();
    } catch {
      // silently fail
    }
  }, [syncBadgeCount]);

  const handleRespondSettlement = async (settlement: PendingSettlement, action: "confirm" | "reject") => {
    setRespondingSettlementId(settlement.id);
    try {
      if (action === "confirm") {
        await settlementsAPI.confirm(settlement.group_id, settlement.id);
      } else {
        await settlementsAPI.reject(settlement.group_id, settlement.id);
      }
      setPendingSettlements((prev) => prev.filter((s) => s.id !== settlement.id));
      syncBadgeCount();
      await Promise.all([fetchGroups(), fetchOverallBalance()]);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setFormError(msg);
    } finally {
      setRespondingSettlementId(null);
    }
  };

  const fetchOverallBalance = useCallback(async () => {
    try {
      const res = await balancesAPI.overall();
      setOverallTotals(res.data.totals_by_currency);
    } catch {
      // silently fail
    }
  }, []);

  const fetchPendingInvitations = useCallback(async () => {
    try {
      const res = await inviteAPI.getMyPendingInvitations();
      setPendingInvitations(res.data);
    } catch {
      // silently fail
    }
  }, []);

  const handleRespondInvitation = async (invitationId: string, action: "accept" | "decline") => {
    setRespondingId(invitationId);
    try {
      await inviteAPI.respondToInvitation(invitationId, action);
      setPendingInvitations((prev) => prev.filter((inv) => inv.id !== invitationId));
      if (action === "accept") {
        await fetchGroups();
      }
    } catch (e: any) {
      console.error("Failed to respond to invitation", e);
    } finally {
      setRespondingId(null);
    }
  };

  const activeGroups = useMemo(() => groups.filter((g) => !g.is_settled), [groups]);
  const settledGroups = useMemo(() => groups.filter((g) => g.is_settled), [groups]);

  const fetchGroups = useCallback(async () => {
    const isFirstLoad = !hasFetched.current;
    if (isFirstLoad) setLoading(true);
    try {
      const res = await groupsAPI.list();
      setGroups(res.data);
      hasFetched.current = true;
    } catch (e) {
      console.error("Failed to fetch groups", e);
    } finally {
      if (isFirstLoad) setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchGroups();
      fetchPendingInvitations();
      fetchPendingSettlements();
      fetchOverallBalance();
    }, [fetchGroups, fetchPendingInvitations, fetchPendingSettlements, fetchOverallBalance])
  );

  // 收到推播時即時刷新首頁所有資料
  useEffect(() => {
    return addNotificationReceivedCallback(() => {
      fetchGroups();
      fetchPendingInvitations();
      fetchPendingSettlements();
      fetchOverallBalance();
    });
  }, [fetchGroups, fetchPendingInvitations, fetchPendingSettlements, fetchOverallBalance]);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchGroups(), fetchPendingInvitations(), fetchPendingSettlements(), fetchOverallBalance()]);
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!newName) return;
    setCreating(true);
    setFormError(null);
    try {
      await groupsAPI.create({
        name: newName,
        description: newDesc || undefined,
        default_currency: newCurrency,
      });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
      setFormError(null);
      await Promise.all([fetchGroups(), fetchOverallBalance()]);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setFormError(msg);
    } finally {
      setCreating(false);
    }
  };

  const handleDragEnd = async ({ data }: { data: GroupItem[] }) => {
    setGroups([...data, ...settledGroups]);
    try {
      await groupsAPI.reorder(data.map((g) => g.id));
    } catch {
      await fetchGroups();
    }
  };

  const closeSwipeable = (id: string) => {
    swipeableRefs.current.get(id)?.close();
  };

  const handleDeleteGroup = (item: GroupItem) => {
    closeSwipeable(item.id);
    setConfirmTarget({ item, action: "delete" });
  };

  const handleLeaveGroup = (item: GroupItem) => {
    closeSwipeable(item.id);
    setConfirmTarget({ item, action: "leave" });
  };

  const handleConfirmAction = async () => {
    if (!confirmTarget) return;
    const { item, action } = confirmTarget;
    setConfirmTarget(null);
    try {
      if (action === "delete") {
        await groupsAPI.delete(item.id);
      } else {
        await groupsAPI.removeMember(item.id, user!.id);
      }
      await Promise.all([fetchGroups(), fetchOverallBalance()]);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setFormError(msg);
    }
  };

  const renderRightActions = (item: GroupItem, dragX: Animated.AnimatedInterpolation<number>) => {
    const isAdmin = item.my_role === "admin";
    const scale = dragX.interpolate({
      inputRange: [-100, 0],
      outputRange: [1, 0.8],
      extrapolate: "clamp",
    });
    return (
      <Animated.View style={{ transform: [{ scale }] }} className="justify-center mb-3">
        <Pressable
          className={`h-full justify-center items-center px-6 rounded-r-xl ${isAdmin ? "bg-destructive" : "bg-warning"}`}
          onPress={() => isAdmin ? handleDeleteGroup(item) : handleLeaveGroup(item)}
        >
          {isAdmin
            ? <Trash size={22} color="white" weight="regular" />
            : <SignOut size={22} color="white" weight="regular" />}
          <Text className="text-white text-xs mt-1 font-medium">
            {isAdmin ? t("delete") : t("leave_group")}
          </Text>
        </Pressable>
      </Animated.View>
    );
  };

  // Compute per-group net balance for the current user (by currency)
  const computeGroupNetBalance = (debts: SimplifiedDebt[]): { currency: string; net: number }[] => {
    if (!user) return [];
    const byCurrency: Record<string, number> = {};
    for (const d of debts) {
      if (!byCurrency[d.currency]) byCurrency[d.currency] = 0;
      if (d.to_user_id === user.id) {
        // someone owes me
        byCurrency[d.currency] += Number(d.amount);
      } else if (d.from_user_id === user.id) {
        // I owe someone
        byCurrency[d.currency] -= Number(d.amount);
      }
    }
    return Object.entries(byCurrency)
      .filter(([, net]) => Math.abs(net) >= 0.01)
      .map(([currency, net]) => ({ currency, net }));
  };

  const renderDebtDetails = (debts: SimplifiedDebt[]) => {
    if (!user) return null;
    // Filter to only show debts involving current user
    const relevantDebts = debts.filter(
      (d) => d.from_user_id === user.id || d.to_user_id === user.id
    );
    if (relevantDebts.length === 0) return null;
    return (
      <View className="px-4 pb-3 -mt-1 gap-1">
        {relevantDebts.map((d, i) => {
          const owesMe = d.to_user_id === user.id;
          const otherName = owesMe ? d.from_user_name : d.to_user_name;
          return (
            <View key={i} className="flex-row items-center pl-9 gap-1">
              <Text className="text-sm text-muted-foreground">
                {owesMe
                  ? t("owes_you", { name: otherName })
                  : t("you_owe_person", { name: otherName })}
              </Text>
              <Text className={`text-sm font-semibold ${owesMe ? "text-income" : "text-destructive"}`}>
                {d.currency} {Number(d.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            </View>
          );
        })}
      </View>
    );
  };

  const renderGroupBalance = (item: GroupItem) => {
    const netBalances = computeGroupNetBalance(item.unsettled_debts);
    if (netBalances.length === 0) {
      return <Muted className="text-xs text-right">{t("balanced")}</Muted>;
    }
    return (
      <View className="items-end">
        {netBalances.map(({ currency, net }, i) => (
          <View key={i} className="items-end">
            <Text className={`text-xs ${net > 0 ? "text-income" : "text-destructive"}`}>
              {net > 0 ? t("you_are_owed") : t("you_owe")}
            </Text>
            <Text className={`text-base font-bold ${net > 0 ? "text-income" : "text-destructive"}`}>
              {currency} {Math.abs(net).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  const renderGroup = ({ item, drag, isActive }: RenderItemParams<GroupItem>) => (
    <ScaleDecorator>
      <Swipeable
        ref={(ref) => {
          if (ref) swipeableRefs.current.set(item.id, ref);
          else swipeableRefs.current.delete(item.id);
        }}
        renderRightActions={(_, dragX) => renderRightActions(item, dragX)}
        rightThreshold={40}
        overshootRight={false}
        enabled={!isActive}
      >
        <Card
          className="mb-3"
          onPress={() => router.push(`/group/${item.id}`)}
        >
          <CardContent className="flex-row items-center justify-between p-4">
            <Pressable
              onLongPress={drag}
              delayLongPress={150}
              hitSlop={8}
              className="justify-center mr-3"
            >
              <DotsSixVertical size={20} color={iconColor} />
            </Pressable>
            <View className="flex-1 gap-1">
              <H3>{item.name}</H3>
              {item.description ? (
                <Muted numberOfLines={1}>{item.description}</Muted>
              ) : null}
              <Muted>{item.member_count} {t("members")}</Muted>
            </View>
            {renderGroupBalance(item)}
          </CardContent>
          {item.unsettled_debts.length > 0 ? renderDebtDetails(item.unsettled_debts) : null}
        </Card>
      </Swipeable>
    </ScaleDecorator>
  );

  const renderSettledGroup = (item: GroupItem) => (
    <Swipeable
      key={item.id}
      ref={(ref) => {
        if (ref) swipeableRefs.current.set(item.id, ref);
        else swipeableRefs.current.delete(item.id);
      }}
      renderRightActions={(_, dragX) => renderRightActions(item, dragX)}
      rightThreshold={40}
      overshootRight={false}
    >
      <Card
        className="mb-3 opacity-70"
        onPress={() => router.push(`/group/${item.id}`)}
      >
        <CardContent className="flex-row items-center justify-between p-4">
          <View className="flex-1 gap-1">
            <H3>{item.name}</H3>
            {item.description ? (
              <Muted numberOfLines={1}>{item.description}</Muted>
            ) : null}
          </View>
          <Muted className="text-xs">{t("balanced")}</Muted>
        </CardContent>
      </Card>
    </Swipeable>
  );

  const settledFooter = settledGroups.length > 0 ? (
    <View className="mt-4">
      <Muted className="text-center text-xs mb-3">{t("hiding_settled_groups")}</Muted>
      <Pressable
        className="self-center border border-primary/30 rounded-full px-5 py-2"
        onPress={() => setSettledExpanded((v) => !v)}
      >
        <Text className="text-primary font-medium text-sm">
          {settledExpanded
            ? t("settled_groups")
            : t("show_settled_groups", { count: settledGroups.length })}
        </Text>
      </Pressable>
      {settledExpanded ? (
        <View className="mt-3">{settledGroups.map(renderSettledGroup)}</View>
      ) : null}
    </View>
  ) : null;

  return (
    <View className="flex-1 bg-background">
      {loading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" />
        </View>
      ) : groups.length === 0 ? (
        <View className="flex-1 items-center justify-center p-5">
          <EmptyState
            icon={UsersThree}
            title={t("create_group")}
            description={t("create_group_hint")}
            actionLabel={t("create_group")}
            onAction={() => setShowCreate(true)}
          />
        </View>
      ) : (
        <DraggableFlatList
          data={activeGroups}
          keyExtractor={(item) => item.id}
          renderItem={renderGroup}
          onDragEnd={handleDragEnd}
          contentContainerStyle={{ padding: 20 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListHeaderComponent={
            <>
              {overallTotals.length > 0 ? (
                <View className="mb-4">
                  {overallTotals.map((ct, i) => {
                    const net = Number(ct.net_balance);
                    const isPositive = net > 0;
                    const isZero = Math.abs(net) < 0.01;
                    return (
                      <View key={i} className="flex-row items-baseline gap-1">
                        <Text className="text-lg font-medium text-foreground">
                          {isZero
                            ? t("overall_all_settled")
                            : isPositive
                              ? t("overall_you_are_owed")
                              : t("overall_you_owe")}
                        </Text>
                        {!isZero && (
                          <Text className={`text-xl font-bold ${isPositive ? "text-income" : "text-destructive"}`}>
                            {ct.currency} {Math.abs(net).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </Text>
                        )}
                      </View>
                    );
                  })}
                </View>
              ) : null}
              {pendingSettlements.length > 0 ? (
                <View className="mb-4">
                  <Muted className="mb-2 text-sm font-medium">{t("pending_settlements")}</Muted>
                  {pendingSettlements.map((s) => (
                    <Card key={s.id} className="mb-2">
                      <CardContent className="p-4 gap-2">
                        <View className="flex-row items-center gap-3">
                          <View className="h-10 w-10 rounded-full bg-income/10 items-center justify-center">
                            <CurrencyCircleDollar size={20} color="hsl(142 71% 45%)" weight="regular" />
                          </View>
                          <View className="flex-1">
                            <Text className="font-medium">
                              {t("settlement_from", { name: s.from_user_name })}
                            </Text>
                            <Muted className="text-xs">
                              {s.group_name ? t("settlement_in_group", { group: s.group_name }) : ""}
                            </Muted>
                          </View>
                          <Text className="text-lg font-bold text-primary">
                            {s.currency} {Number(s.amount).toLocaleString()}
                          </Text>
                        </View>
                        {s.original_currency && s.original_amount && (
                          <View className="bg-muted/50 rounded-lg px-3 py-2">
                            <Text className="text-xs text-muted-foreground">
                              {t("settlement_converted_from", {
                                original_currency: s.original_currency,
                                original_amount: Number(s.original_amount).toLocaleString(),
                              })}
                            </Text>
                            <Text className="text-xs text-muted-foreground">
                              {t("settlement_actual_pay", {
                                currency: s.currency,
                                amount: Number(s.amount).toLocaleString(),
                              })}
                            </Text>
                          </View>
                        )}
                        <View className="flex-row gap-2 mt-1">
                          <Button
                            size="sm"
                            className="flex-1"
                            onPress={() => handleRespondSettlement(s, "confirm")}
                            loading={respondingSettlementId === s.id}
                            disabled={respondingSettlementId !== null}
                          >
                            {t("confirm_settlement")}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1"
                            onPress={() => handleRespondSettlement(s, "reject")}
                            disabled={respondingSettlementId !== null}
                          >
                            {t("reject_settlement")}
                          </Button>
                        </View>
                      </CardContent>
                    </Card>
                  ))}
                </View>
              ) : null}
              {pendingInvitations.length > 0 ? (
                <View className="mb-4">
                  <Muted className="mb-2 text-sm font-medium">{t("pending_invitations")}</Muted>
                  {pendingInvitations.map((inv) => (
                    <Card key={inv.id} className="mb-2">
                      <CardContent className="p-4 gap-2">
                        <View className="flex-row items-center gap-3">
                          <View className="h-10 w-10 rounded-full bg-primary/10 items-center justify-center">
                            <EnvelopeSimple size={20} color="hsl(240 3.8% 46.1%)" weight="regular" />
                          </View>
                          <View className="flex-1">
                            <Text className="font-medium">{inv.group_name}</Text>
                            <Muted className="text-xs">
                              {t("invited_by", { name: inv.inviter_name })} · {inv.member_count} {t("members_count")}
                            </Muted>
                          </View>
                        </View>
                        <View className="flex-row gap-2 mt-1">
                          <Button
                            size="sm"
                            className="flex-1"
                            onPress={() => handleRespondInvitation(inv.id, "accept")}
                            loading={respondingId === inv.id}
                            disabled={respondingId === inv.id}
                          >
                            {t("accept_invitation")}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1"
                            onPress={() => handleRespondInvitation(inv.id, "decline")}
                            disabled={respondingId === inv.id}
                          >
                            {t("decline_invitation")}
                          </Button>
                        </View>
                      </CardContent>
                    </Card>
                  ))}
                </View>
              ) : null}
            </>
          }
          ListFooterComponent={settledFooter}
        />
      )}

      <FAB onPress={() => setShowCreate(true)} />

      <Modal
        visible={!!confirmTarget}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmTarget(null)}
      >
        <View className={`flex-1 ${themeClass}`}>
        <View className="flex-1 justify-center items-center bg-black/50 px-6">
          <View className="bg-background rounded-xl p-6 w-full max-w-sm gap-4">
            <H3>
              {confirmTarget?.action === "delete" ? t("delete_group") : t("leave_group")}
            </H3>
            <Text className="text-muted-foreground">
              {confirmTarget?.action === "delete" ? t("delete_group_confirm") : t("leave_group_confirm")}
            </Text>
            <View className="flex-row gap-3 justify-end">
              <Button variant="outline" onPress={() => setConfirmTarget(null)}>
                {t("cancel")}
              </Button>
              <Button variant="destructive" onPress={handleConfirmAction}>
                {confirmTarget?.action === "delete" ? t("delete") : t("leave_group")}
              </Button>
            </View>
          </View>
        </View>
        </View>
      </Modal>

      <Modal
        visible={showCreate}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCreate(false)}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View className="flex-1 justify-end bg-black/50">
            <View className="bg-background rounded-t-2xl px-5 pb-10 pt-4">
              <View className="items-center mb-4">
                <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
              </View>

              <View className="flex-row items-center justify-between mb-6">
                <H3>{t("create_group")}</H3>
                <Pressable onPress={() => setShowCreate(false)}>
                  <X size={24} color={iconColor} />
                </Pressable>
              </View>

              <View className="gap-4">
                <Input
                  label={t("group_name")}
                  value={newName}
                  onChangeText={(v) => { setNewName(v); setFormError(null); }}
                  placeholder={t("group_name")}
                />
                <Input
                  label={t("description")}
                  value={newDesc}
                  onChangeText={setNewDesc}
                  placeholder={t("description")}
                />
                <CurrencyPicker
                  label={t("default_currency")}
                  value={newCurrency}
                  onSelect={setNewCurrency}
                />

                {formError ? (
                  <Text className="text-destructive text-sm">{formError}</Text>
                ) : null}

                <Button
                  onPress={handleCreate}
                  loading={creating}
                  disabled={creating || !newName}
                  size="lg"
                  className="mt-2"
                >
                  {t("save")}
                </Button>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
        </View>
      </Modal>
    </View>
  );
}
