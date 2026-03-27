import { useCallback, useState } from "react";
import { View, StyleSheet, FlatList, RefreshControl } from "react-native";
import {
  FAB,
  Card,
  Text,
  Chip,
  Button,
  Portal,
  Modal,
  TextInput,
  SegmentedButtons,
} from "react-native-paper";
import { useLocalSearchParams, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { expensesAPI, settlementsAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";

type Tab = "expenses" | "settlements";

interface ExpenseItem {
  id: string;
  description: string;
  total_amount: string;
  currency: string;
  payer_display_name: string;
  split_method: string;
  created_at: string;
}

interface Suggestion {
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  amount: string;
  currency: string;
}

export default function GroupDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  const [tab, setTab] = useState<Tab>("expenses");
  const [expenses, setExpenses] = useState<ExpenseItem[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Add expense modal
  const [showAdd, setShowAdd] = useState(false);
  const [desc, setDesc] = useState("");
  const [amount, setAmount] = useState("");
  const [splitMethod, setSplitMethod] = useState("equal");
  const [adding, setAdding] = useState(false);

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      const [expRes, sugRes] = await Promise.all([
        expensesAPI.list(id),
        settlementsAPI.suggestions(id),
      ]);
      setExpenses(expRes.data);
      setSuggestions(sugRes.data);
    } catch (e) {
      console.error("Failed to fetch group data", e);
    }
  }, [id]);

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [fetchData])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleAddExpense = async () => {
    if (!desc || !amount || !id || !user) return;
    setAdding(true);
    try {
      await expensesAPI.create(id, {
        description: desc,
        total_amount: parseFloat(amount),
        paid_by: user.id,
        split_method: splitMethod,
      });
      setShowAdd(false);
      setDesc("");
      setAmount("");
      await fetchData();
    } catch (e) {
      console.error("Failed to add expense", e);
    } finally {
      setAdding(false);
    }
  };

  const renderExpense = ({ item }: { item: ExpenseItem }) => (
    <Card style={styles.card}>
      <Card.Title
        title={item.description}
        subtitle={`${item.payer_display_name} ${t("paid_by")}`}
        right={() => (
          <View style={styles.amountContainer}>
            <Text variant="titleMedium" style={styles.amount}>
              {item.currency} {parseFloat(item.total_amount).toLocaleString()}
            </Text>
            <Chip compact style={styles.methodChip}>
              {t(item.split_method)}
            </Chip>
          </View>
        )}
      />
    </Card>
  );

  const renderSuggestion = ({ item }: { item: Suggestion }) => (
    <Card style={styles.card}>
      <Card.Content style={styles.suggestionContent}>
        <Text variant="bodyLarge">
          <Text style={styles.debtorName}>{item.from_user_name}</Text>
          {" "}{t("owes")}{" "}
          <Text style={styles.creditorName}>{item.to_user_name}</Text>
        </Text>
        <Text variant="titleMedium" style={styles.suggestionAmount}>
          {item.currency} {parseFloat(item.amount).toLocaleString()}
        </Text>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <SegmentedButtons
        value={tab}
        onValueChange={(v) => setTab(v as Tab)}
        buttons={[
          { value: "expenses", label: t("expenses") },
          { value: "settlements", label: t("settlements") },
        ]}
        style={styles.tabs}
      />

      {tab === "expenses" ? (
        <FlatList
          data={expenses}
          keyExtractor={(item) => item.id}
          renderItem={renderExpense}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <Text style={styles.empty}>{t("add_expense")}</Text>
          }
        />
      ) : (
        <FlatList
          data={suggestions}
          keyExtractor={(_, i) => `s-${i}`}
          renderItem={renderSuggestion}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <Text style={styles.empty}>{t("balanced")}</Text>
          }
        />
      )}

      {tab === "expenses" && (
        <FAB
          icon="plus"
          style={styles.fab}
          onPress={() => setShowAdd(true)}
        />
      )}

      <Portal>
        <Modal
          visible={showAdd}
          onDismiss={() => setShowAdd(false)}
          contentContainerStyle={styles.modal}
        >
          <Text variant="titleLarge" style={styles.modalTitle}>
            {t("add_expense")}
          </Text>
          <TextInput
            label={t("description")}
            value={desc}
            onChangeText={setDesc}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label={t("amount")}
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
            mode="outlined"
            style={styles.input}
          />
          <Text variant="bodyMedium" style={styles.splitLabel}>
            {t("split_method")}
          </Text>
          <SegmentedButtons
            value={splitMethod}
            onValueChange={setSplitMethod}
            buttons={[
              { value: "equal", label: t("equal") },
              { value: "ratio", label: t("ratio") },
              { value: "exact", label: t("exact") },
              { value: "shares", label: t("shares") },
            ]}
            style={styles.splitButtons}
          />
          <Button
            mode="contained"
            onPress={handleAddExpense}
            loading={adding}
            disabled={adding || !desc || !amount}
            style={styles.addBtn}
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
  tabs: { margin: 16 },
  list: { paddingHorizontal: 16, paddingBottom: 80 },
  card: { marginBottom: 10, backgroundColor: "#fff" },
  amountContainer: { alignItems: "flex-end", marginRight: 16 },
  amount: { fontWeight: "bold", color: "#2563EB" },
  methodChip: { marginTop: 4 },
  suggestionContent: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  debtorName: { fontWeight: "bold", color: "#EF4444" },
  creditorName: { fontWeight: "bold", color: "#059669" },
  suggestionAmount: { fontWeight: "bold", color: "#2563EB" },
  empty: { textAlign: "center", color: "#999", marginTop: 40 },
  fab: { position: "absolute", right: 16, bottom: 16, backgroundColor: "#2563EB" },
  modal: { backgroundColor: "#fff", padding: 24, margin: 24, borderRadius: 12 },
  modalTitle: { marginBottom: 16 },
  input: { marginBottom: 12 },
  splitLabel: { marginBottom: 8, color: "#666" },
  splitButtons: { marginBottom: 16 },
  addBtn: { marginTop: 8 },
});
