import { useCallback, useState } from "react";
import { View, FlatList, RefreshControl, Modal, Pressable } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { Users, X } from "lucide-react-native";
import { groupsAPI } from "../../services/api";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";

interface GroupItem {
  id: string;
  name: string;
  description: string | null;
  default_currency: string;
  member_count: number;
  created_at: string;
}

export default function GroupsScreen() {
  const { t } = useTranslation();
  const [groups, setGroups] = useState<GroupItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCurrency, setNewCurrency] = useState("TWD");
  const [creating, setCreating] = useState(false);

  const fetchGroups = useCallback(async () => {
    try {
      const res = await groupsAPI.list();
      setGroups(res.data);
    } catch (e) {
      console.error("Failed to fetch groups", e);
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
    } catch (e) {
      console.error("Failed to create group", e);
    } finally {
      setCreating(false);
    }
  };

  const renderGroup = ({ item }: { item: GroupItem }) => (
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
  );

  return (
    <View className="flex-1 bg-background">
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
            description="建立一個群組開始分帳吧！"
            actionLabel={t("create_group")}
            onAction={() => setShowCreate(true)}
          />
        }
      />

      <FAB onPress={() => setShowCreate(true)} />

      <Modal
        visible={showCreate}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCreate(false)}
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
              <Input
                label={t("default_currency")}
                value={newCurrency}
                onChangeText={setNewCurrency}
                placeholder="TWD"
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
      </Modal>
    </View>
  );
}
