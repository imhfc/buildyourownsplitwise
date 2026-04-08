import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { View, FlatList, RefreshControl, Modal, Pressable, KeyboardAvoidingView, Platform, Animated, ActivityIndicator, ScrollView } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { SquaresFour, X, Trash, SignOut, DotsSixVertical, CaretDown, CaretRight, EnvelopeSimple, Check, CurrencyCircleDollar } from "phosphor-react-native";
import { Swipeable } from "react-native-gesture-handler";
import DraggableFlatList, { ScaleDecorator, RenderItemParams } from "react-native-draggable-flatlist";
import { groupsAPI, inviteAPI, settlementsAPI, balancesAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { usePendingSettlementsStore } from "../../stores/pending-settlements";
import { useDraftStore } from "../../stores/draft";
import { DiscardDraftDialog } from "~/components/ui/discard-draft-dialog";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { CurrencyPicker } from "~/components/ui/currency-picker";
import { Separator } from "~/components/ui/separator";
import { useThemeClassName, useTheme } from "~/lib/theme";
import { Logo } from "~/components/Logo";
import { addNotificationReceivedCallback } from "~/lib/notifications";

interface SimplifiedDebt {
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  amount: number;
  currency: string;
}

interface GroupMember {
  user: { id: string; display_name: string; email: string };
  role: string;
}

interface GroupItem {
  id: string;
  name: string;
  description: string | null;
  default_currency: string;
  member_count: number;
  admin_count: number;
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
  const iconColor = isDark ? "#737373" : "#A3A3A3";
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
  const [adminTransferTarget, setAdminTransferTarget] = useState<GroupItem | null>(null);
  const [adminTransferMembers, setAdminTransferMembers] = useState<GroupMember[]>([]);
  const [adminTransferLoading, setAdminTransferLoading] = useState(false);
  const [settledExpanded, setSettledExpanded] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [overallTotals, setOverallTotals] = useState<CurrencyTotal[]>([]);
  const [showDiscardConfirm, setShowDiscardConfirm] = useState(false);
  const { saveDraft, getDraft, clearDraft } = useDraftStore();
  const CREATE_DRAFT_KEY = "create-group";

  const isCreateDirty = !!(newName || newDesc);

  const handleOpenCreate = () => {
    const draft = getDraft(CREATE_DRAFT_KEY);
    if (draft) {
      setNewName((draft.newName as string) || "");
      setNewDesc((draft.newDesc as string) || "");
      if (draft.newCurrency) setNewCurrency(draft.newCurrency as string);
    }
    setShowCreate(true);
  };

  const handleCloseCreate = () => {
    if (isCreateDirty) {
      setShowDiscardConfirm(true);
    } else {
      resetAndCloseCreate();
    }
  };

  const handleDiscardCreate = () => {
    saveDraft(CREATE_DRAFT_KEY, { newName, newDesc, newCurrency });
    setShowDiscardConfirm(false);
    resetAndCloseCreate();
  };

  const resetAndCloseCreate = () => {
    setShowCreate(false);
    setNewName("");
    setNewDesc("");
    setFormError(null);
  };

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
      clearDraft(CREATE_DRAFT_KEY);
      resetAndCloseCreate();
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

  const handleLeaveGroup = async (item: GroupItem) => {
    closeSwipeable(item.id);
    const isOnlyAdmin = item.my_role === "admin" && item.admin_count <= 1 && item.member_count > 1;
    if (isOnlyAdmin) {
      // 唯一 admin 且有其他成員：拉取成員列表讓使用者選擇新群主
      setAdminTransferLoading(true);
      setAdminTransferTarget(item);
      try {
        const res = await groupsAPI.get(item.id);
        const members: GroupMember[] = res.data.members.filter(
          (m: GroupMember) => m.user.id !== user!.id
        );
        setAdminTransferMembers(members);
      } catch (e: any) {
        const msg = e.response?.data?.detail || e.message || t("unknown_error");
        setFormError(msg);
        setAdminTransferTarget(null);
      } finally {
        setAdminTransferLoading(false);
      }
    } else {
      setConfirmTarget({ item, action: "leave" });
    }
  };

  const handleSelectNewAdmin = async (newAdminId: string) => {
    if (!adminTransferTarget || !user) return;
    setAdminTransferLoading(true);
    try {
      await groupsAPI.removeMember(adminTransferTarget.id, user.id, newAdminId);
      setAdminTransferTarget(null);
      setAdminTransferMembers([]);
      await Promise.all([fetchGroups(), fetchOverallBalance()]);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setFormError(msg);
    } finally {
      setAdminTransferLoading(false);
    }
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
      inputRange: [isAdmin ? -200 : -130, 0],
      outputRange: [1, 0.8],
      extrapolate: "clamp",
    });
    return (
      <Animated.View style={{ transform: [{ scale }], flexDirection: "row", marginLeft: 8, marginBottom: 8 }}>
        {isAdmin && (
          <Pressable
            style={{ justifyContent: "center", alignItems: "center", paddingHorizontal: 20, backgroundColor: "#f59e0b", borderTopLeftRadius: 12, borderBottomLeftRadius: 12 }}
            onPress={() => handleLeaveGroup(item)}
          >
            <SignOut size={18} color="white" weight="regular" />
            <Text className="text-white text-xs mt-0.5 font-medium">
              {t("leave_group")}
            </Text>
          </Pressable>
        )}
        <Pressable
          style={{
            justifyContent: "center", alignItems: "center", paddingHorizontal: 20,
            backgroundColor: isAdmin ? "#ef4444" : "#f59e0b",
            borderTopLeftRadius: isAdmin ? 0 : 12, borderBottomLeftRadius: isAdmin ? 0 : 12,
            borderTopRightRadius: 12, borderBottomRightRadius: 12,
          }}
          onPress={() => isAdmin ? handleDeleteGroup(item) : handleLeaveGroup(item)}
        >
          {isAdmin
            ? <Trash size={18} color="white" weight="regular" />
            : <SignOut size={18} color="white" weight="regular" />}
          <Text className="text-white text-xs mt-0.5 font-medium">
            {isAdmin ? t("delete") : t("leave_group")}
          </Text>
        </Pressable>
      </Animated.View>
    );
  };

  const computeGroupNetBalance = (debts: SimplifiedDebt[]): { currency: string; net: number }[] => {
    if (!user) return [];
    const byCurrency: Record<string, number> = {};
    for (const d of debts) {
      if (!byCurrency[d.currency]) byCurrency[d.currency] = 0;
      if (d.to_user_id === user.id) {
        byCurrency[d.currency] += Number(d.amount);
      } else if (d.from_user_id === user.id) {
        byCurrency[d.currency] -= Number(d.amount);
      }
    }
    return Object.entries(byCurrency)
      .filter(([, net]) => Math.abs(net) >= 0.01)
      .map(([currency, net]) => ({ currency, net }));
  };

  const renderDebtDetails = (debts: SimplifiedDebt[]) => {
    if (!user) return null;
    const relevantDebts = debts.filter(
      (d) => d.from_user_id === user.id || d.to_user_id === user.id
    );
    if (relevantDebts.length === 0) return null;
    return (
      <View className="px-4 pb-3 gap-1">
        {relevantDebts.map((d, i) => {
          const owesMe = d.to_user_id === user.id;
          const otherName = owesMe ? d.from_user_name : d.to_user_name;
          return (
            <View key={i} className="flex-row items-center pl-7 gap-1">
              <Text className="text-xs text-muted-foreground">
                {owesMe
                  ? t("owes_you", { name: otherName })
                  : t("you_owe_person", { name: otherName })}
              </Text>
              <Text className={`text-xs font-medium ${owesMe ? "text-income" : "text-destructive"}`}>
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
      return <Muted className="text-xs">{t("balanced")}</Muted>;
    }
    return (
      <View className="items-end">
        {netBalances.map(({ currency, net }, i) => (
          <View key={i} className="items-end">
            <Text className={`text-xs ${net > 0 ? "text-income" : "text-destructive"}`}>
              {net > 0 ? t("you_are_owed") : t("you_owe")}
            </Text>
            <Text className={`text-sm font-semibold tabular-nums ${net > 0 ? "text-income" : "text-destructive"}`}>
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
          className="mb-2"
          onPress={() => router.push(`/group/${item.id}`)}
        >
          <CardContent className="flex-row items-center justify-between p-3.5">
            <Pressable
              onLongPress={drag}
              delayLongPress={150}
              hitSlop={8}
              className="justify-center mr-2.5"
            >
              <DotsSixVertical size={18} color={iconColor} />
            </Pressable>
            <View className="flex-1 gap-0.5">
              <Text className="text-sm font-medium text-foreground">{item.name}</Text>
              {item.description ? (
                <Text className="text-xs text-muted-foreground" numberOfLines={1}>{item.description}</Text>
              ) : null}
              <Text className="text-xs text-muted-foreground">{item.member_count} {t("members")}</Text>
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
        className="mb-2 opacity-60"
        onPress={() => router.push(`/group/${item.id}`)}
      >
        <CardContent className="flex-row items-center justify-between p-3.5">
          <View className="flex-1 gap-0.5">
            <Text className="text-sm font-medium text-foreground">{item.name}</Text>
            {item.description ? (
              <Text className="text-xs text-muted-foreground" numberOfLines={1}>{item.description}</Text>
            ) : null}
          </View>
          <Muted className="text-xs">{t("balanced")}</Muted>
        </CardContent>
      </Card>
    </Swipeable>
  );

  /* ── Overall Balance Header ── */
  const balanceHeader = overallTotals.length > 0 ? (
    <View className="mb-6">
      {overallTotals.map((ct, i) => {
        const net = Number(ct.net_balance);
        const isPositive = net > 0;
        const isZero = Math.abs(net) < 0.01;
        return (
          <View key={i} className="flex-row items-baseline gap-1.5">
            <Text className="text-sm text-muted-foreground">
              {isZero
                ? t("overall_all_settled")
                : isPositive
                  ? t("overall_you_are_owed")
                  : t("overall_you_owe")}
            </Text>
            {!isZero && (
              <Text className={`text-lg font-semibold tabular-nums ${isPositive ? "text-income" : "text-destructive"}`}>
                {ct.currency} {Math.abs(net).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            )}
          </View>
        );
      })}
    </View>
  ) : null;

  /* ── Pending Settlements ── */
  const settlementsSection = pendingSettlements.length > 0 ? (
    <View className="mb-5">
      <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        {t("pending_settlements")}
      </Text>
      {pendingSettlements.map((s) => (
        <Card key={s.id} className="mb-2">
          <CardContent className="p-3.5 gap-2.5">
            <View className="flex-row items-center justify-between">
              <View className="flex-1">
                <Text className="text-sm font-medium">
                  {t("settlement_from", { name: s.from_user_name })}
                </Text>
                {s.group_name ? (
                  <Text className="text-xs text-muted-foreground mt-0.5">
                    {t("settlement_in_group", { group: s.group_name })}
                  </Text>
                ) : null}
              </View>
              <Text className="text-sm font-semibold tabular-nums text-foreground">
                {s.currency} {Number(s.amount).toLocaleString()}
              </Text>
            </View>
            {s.original_currency && s.original_amount && (
              <View className="bg-muted rounded-md px-3 py-2">
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
            <View className="flex-row gap-2">
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
  ) : null;

  /* ── Pending Invitations ── */
  const invitationsSection = pendingInvitations.length > 0 ? (
    <View className="mb-5">
      <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        {t("pending_invitations")}
      </Text>
      {pendingInvitations.map((inv) => (
        <Card key={inv.id} className="mb-2">
          <CardContent className="p-3.5 gap-2.5">
            <View>
              <Text className="text-sm font-medium">{inv.group_name}</Text>
              <Text className="text-xs text-muted-foreground mt-0.5">
                {t("invited_by", { name: inv.inviter_name })} · {inv.member_count} {t("members_count")}
              </Text>
            </View>
            <View className="flex-row gap-2">
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
  ) : null;

  /* ── Settled Groups Footer ── */
  const settledFooter = settledGroups.length > 0 ? (
    <View className="mt-6">
      <Pressable
        className="self-center"
        onPress={() => setSettledExpanded((v) => !v)}
      >
        <Text className="text-xs text-muted-foreground">
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
            icon={SquaresFour}
            title={t("create_group")}
            description={t("create_group_hint")}
            actionLabel={t("create_group")}
            onAction={handleOpenCreate}
          />
        </View>
      ) : (
        <DraggableFlatList
          data={activeGroups}
          keyExtractor={(item) => item.id}
          renderItem={renderGroup}
          onDragEnd={handleDragEnd}
          contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListHeaderComponent={
            <>
              {balanceHeader}
              {settlementsSection}
              {invitationsSection}
            </>
          }
          ListFooterComponent={
            <>
              {settledFooter}
              <View className="items-center pb-8 pt-6 opacity-30">
                <Logo size={32} />
              </View>
            </>
          }
        />
      )}

      <FAB onPress={handleOpenCreate} />

      {/* ── Delete/Leave Confirm ── */}
      <Modal
        visible={!!confirmTarget}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmTarget(null)}
      >
        <View className={`flex-1 ${themeClass}`}>
        <Pressable className="flex-1 justify-center items-center bg-black/50 px-6" onPress={() => setConfirmTarget(null)}>
          <Pressable className="bg-background rounded-xl border border-border p-6 w-full max-w-sm gap-4">
            <Text className="text-base font-semibold text-foreground">
              {confirmTarget?.action === "delete" ? t("delete_group") : t("leave_group")}
            </Text>
            <Text className="text-sm text-muted-foreground">
              {confirmTarget?.action === "delete" ? t("delete_group_confirm") : t("leave_group_confirm")}
            </Text>
            <View className="flex-row gap-2 justify-end">
              <Button variant="outline" size="sm" onPress={() => setConfirmTarget(null)}>
                {t("cancel")}
              </Button>
              <Button variant="destructive" size="sm" onPress={handleConfirmAction}>
                {confirmTarget?.action === "delete" ? t("delete") : t("leave_group")}
              </Button>
            </View>
          </Pressable>
        </Pressable>
        </View>
      </Modal>

      {/* ── Select New Admin Modal ── */}
      <Modal
        visible={!!adminTransferTarget}
        transparent
        animationType="slide"
        onRequestClose={() => { setAdminTransferTarget(null); setAdminTransferMembers([]); }}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <Pressable className="flex-1" onPress={() => { setAdminTransferTarget(null); setAdminTransferMembers([]); }} />
          <View className="bg-background border-t border-border rounded-t-xl px-5 pb-10 pt-4 max-h-[70%]">
            <View className="items-center mb-4">
              <View className="h-1 w-8 rounded-full bg-muted-foreground/20" />
            </View>
            <View className="flex-row items-center justify-between mb-5">
              <Text className="text-base font-semibold">{t("select_new_admin")}</Text>
              <Pressable onPress={() => { setAdminTransferTarget(null); setAdminTransferMembers([]); }} hitSlop={8}>
                <X size={20} color={isDark ? "#737373" : "#A3A3A3"} />
              </Pressable>
            </View>
            <Text className="text-sm text-muted-foreground mb-4">{t("select_new_admin_desc")}</Text>
            {adminTransferLoading && adminTransferMembers.length === 0 ? (
              <ActivityIndicator className="my-4" />
            ) : (
              <FlatList
                data={adminTransferMembers}
                keyExtractor={(m) => m.user.id}
                renderItem={({ item: m }) => (
                  <Card className="mb-2">
                    <CardContent className="flex-row items-center p-3.5 gap-3">
                      <View className="flex-1 gap-0.5">
                        <Text className="text-sm font-medium text-foreground">{m.user.display_name}</Text>
                        <Text className="text-xs text-muted-foreground">{m.user.email}</Text>
                      </View>
                      <Button
                        size="sm"
                        onPress={() => handleSelectNewAdmin(m.user.id)}
                        disabled={adminTransferLoading}
                        loading={adminTransferLoading}
                      >
                        {t("confirm")}
                      </Button>
                    </CardContent>
                  </Card>
                )}
              />
            )}
          </View>
        </KeyboardAvoidingView>
        </View>
      </Modal>

      {/* ── Create Group Sheet ── */}
      <Modal
        visible={showCreate}
        transparent
        animationType="slide"
        onRequestClose={handleCloseCreate}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <Pressable className="flex-1" onPress={handleCloseCreate} />
          <View className="bg-background border-t border-border rounded-t-xl px-5 pb-10 pt-4">
            <View className="items-center mb-4">
              <View className="h-1 w-8 rounded-full bg-muted-foreground/20" />
            </View>

            <View className="flex-row items-center justify-between mb-5">
              <Text className="text-base font-semibold">{t("create_group")}</Text>
              <Pressable onPress={handleCloseCreate} hitSlop={8}>
                <X size={20} color={isDark ? "#737373" : "#A3A3A3"} />
              </Pressable>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
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
                  className="mt-1"
                >
                  {t("save")}
                </Button>
              </View>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
        </View>
      </Modal>

      <DiscardDraftDialog
        visible={showDiscardConfirm}
        onDiscard={handleDiscardCreate}
        onCancel={() => setShowDiscardConfirm(false)}
      />
    </View>
  );
}
