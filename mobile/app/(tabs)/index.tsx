import { useCallback, useMemo, useRef, useState } from "react";
import { View, RefreshControl, Modal, Pressable, KeyboardAvoidingView, Platform, Animated, ActivityIndicator } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { UsersThree, X, Trash, SignOut, DotsSixVertical, CaretDown, CaretRight, EnvelopeSimple, Check } from "phosphor-react-native";
import { Swipeable } from "react-native-gesture-handler";
import DraggableFlatList, { ScaleDecorator, RenderItemParams } from "react-native-draggable-flatlist";
import { groupsAPI, inviteAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { CurrencyPicker } from "~/components/ui/currency-picker";
import { useThemeClassName, useTheme } from "~/lib/theme";

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

export default function GroupsScreen() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const themeClass = useThemeClassName();
  const { isDark } = useTheme();
  const iconColor = isDark ? "#A1A1AA" : "#71717A";
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
    }, [fetchGroups, fetchPendingInvitations])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchGroups(), fetchPendingInvitations()]);
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
      await fetchGroups();
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
      await fetchGroups();
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

  const renderDebtDetails = (debts: SimplifiedDebt[]) => (
    <View className="px-4 pb-3 -mt-2 gap-2">
      {debts.map((d, i) => (
        <View key={i} className="pl-9">
          <Text className="text-sm text-muted-foreground">
            {d.from_user_name} {t("owes")} {d.to_user_name}
          </Text>
          <Text className="text-lg font-bold text-destructive">
            {d.currency} {Number(d.amount).toFixed(2)}
          </Text>
        </View>
      ))}
    </View>
  );

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
            <Badge>{item.default_currency}</Badge>
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
        className="mb-3"
        onPress={() => router.push(`/group/${item.id}`)}
      >
        <CardContent className="flex-row items-center justify-between p-4">
          <View className="flex-1 gap-1">
            <H3>{item.name}</H3>
            {item.description ? (
              <Muted numberOfLines={1}>{item.description}</Muted>
            ) : null}
            <Muted className="text-green-600">{t("balanced")}</Muted>
          </View>
          <Badge>{item.default_currency}</Badge>
        </CardContent>
      </Card>
    </Swipeable>
  );

  const settledFooter = settledGroups.length > 0 ? (
    <View className="mt-2">
      <Pressable
        className="flex-row items-center gap-2 py-3 px-1"
        onPress={() => setSettledExpanded((v) => !v)}
      >
        {settledExpanded
          ? <CaretDown size={18} color={iconColor} />
          : <CaretRight size={18} color={iconColor} />}
        <Text className="text-muted-foreground font-medium">
          {t("settled_groups")} ({settledGroups.length})
        </Text>
      </Pressable>
      {settledExpanded ? settledGroups.map(renderSettledGroup) : null}
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
            pendingInvitations.length > 0 ? (
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
            ) : null
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
