import { useCallback, useRef, useState } from "react";
import { View, FlatList, RefreshControl, Modal, Pressable, Alert, KeyboardAvoidingView, Platform, Animated, ActivityIndicator } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { Users, X, Trash2, LogOut } from "lucide-react-native";
import { Swipeable } from "react-native-gesture-handler";
import { groupsAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { CurrencyPicker } from "~/components/ui/currency-picker";

interface GroupItem {
  id: string;
  name: string;
  description: string | null;
  default_currency: string;
  member_count: number;
  created_at: string;
  created_by: string;
  my_role: string;
}

export default function GroupsScreen() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
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
    }, [fetchGroups])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchGroups();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (!newName) return;
    setCreating(true);
    try {
      await groupsAPI.create({
        name: newName,
        description: newDesc || undefined,
        default_currency: newCurrency,
      });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
      await fetchGroups();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || "Unknown error";
      Alert.alert(t("error"), msg);
    } finally {
      setCreating(false);
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
      const msg = e.response?.data?.detail || e.message || "Unknown error";
      Alert.alert(t("error"), msg);
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
          className={`h-full justify-center items-center px-6 rounded-r-xl ${isAdmin ? "bg-destructive" : "bg-orange-500"}`}
          onPress={() => isAdmin ? handleDeleteGroup(item) : handleLeaveGroup(item)}
        >
          {isAdmin
            ? <Trash2 size={22} color="white" />
            : <LogOut size={22} color="white" />}
          <Text className="text-white text-xs mt-1 font-medium">
            {isAdmin ? t("delete") : t("leave_group")}
          </Text>
        </Pressable>
      </Animated.View>
    );
  };

  const renderGroup = ({ item }: { item: GroupItem }) => (
    <Swipeable
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
            <Muted>{item.member_count} {t("members")}</Muted>
          </View>
          <Badge>{item.default_currency}</Badge>
        </CardContent>
      </Card>
    </Swipeable>
  );

  return (
    <View className="flex-1 bg-background">
      {loading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" />
        </View>
      ) : (
        <FlatList
          data={groups}
          keyExtractor={(item) => item.id}
          renderItem={renderGroup}
          contentContainerStyle={{ padding: 20 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <EmptyState
              icon={Users}
              title={t("create_group")}
              description={t("create_group_hint")}
              actionLabel={t("create_group")}
              onAction={() => setShowCreate(true)}
            />
          }
        />
      )}

      <FAB onPress={() => setShowCreate(true)} />

      <Modal
        visible={!!confirmTarget}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmTarget(null)}
      >
        <View className="flex-1 justify-center items-center bg-black/50 px-6">
          <View className="bg-background rounded-2xl p-6 w-full max-w-sm gap-4">
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
      </Modal>

      <Modal
        visible={showCreate}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCreate(false)}
      >
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View className="flex-1 justify-end bg-black/50">
            <View className="bg-background rounded-t-3xl px-5 pb-10 pt-4">
              <View className="items-center mb-4">
                <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
              </View>

              <View className="flex-row items-center justify-between mb-6">
                <H3>{t("create_group")}</H3>
                <Pressable onPress={() => setShowCreate(false)}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              <View className="gap-4">
                <Input
                  label={t("group_name")}
                  value={newName}
                  onChangeText={setNewName}
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
      </Modal>
    </View>
  );
}
