import { useCallback, useState } from "react";
import { View, StyleSheet, FlatList, RefreshControl } from "react-native";
import { FAB, Card, Text, Chip, Portal, Modal, TextInput, Button } from "react-native-paper";
import { router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { groupsAPI } from "../../services/api";

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
      style={styles.card}
      onPress={() => router.push(`/group/${item.id}`)}
    >
      <Card.Title
        title={item.name}
        subtitle={item.description}
        right={() => (
          <View style={styles.cardRight}>
            <Chip compact>{item.default_currency}</Chip>
            <Text variant="bodySmall" style={styles.memberCount}>
              {item.member_count} {t("members")}
            </Text>
          </View>
        )}
      />
    </Card>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={groups}
        keyExtractor={(item) => item.id}
        renderItem={renderGroup}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <Text style={styles.empty}>{t("create_group")}</Text>
        }
      />

      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => setShowCreate(true)}
      />

      <Portal>
        <Modal
          visible={showCreate}
          onDismiss={() => setShowCreate(false)}
          contentContainerStyle={styles.modal}
        >
          <Text variant="titleLarge" style={styles.modalTitle}>
            {t("create_group")}
          </Text>
          <TextInput
            label={t("group_name")}
            value={newName}
            onChangeText={setNewName}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label={t("description")}
            value={newDesc}
            onChangeText={setNewDesc}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label={t("default_currency")}
            value={newCurrency}
            onChangeText={setNewCurrency}
            mode="outlined"
            style={styles.input}
          />
          <Button
            mode="contained"
            onPress={handleCreate}
            loading={creating}
            disabled={creating || !newName}
            style={styles.createBtn}
          >
            {t("save")}
          </Button>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F5F5" },
  list: { padding: 16 },
  card: { marginBottom: 12, backgroundColor: "#fff" },
  cardRight: { alignItems: "flex-end", marginRight: 16 },
  memberCount: { color: "#999", marginTop: 4 },
  empty: { textAlign: "center", color: "#999", marginTop: 40 },
  fab: { position: "absolute", right: 16, bottom: 16, backgroundColor: "#2563EB" },
  modal: { backgroundColor: "#fff", padding: 24, margin: 24, borderRadius: 12 },
  modalTitle: { marginBottom: 16 },
  input: { marginBottom: 12 },
  createBtn: { marginTop: 8 },
});
