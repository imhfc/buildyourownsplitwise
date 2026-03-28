import { useCallback, useState } from "react";
import { View, FlatList, RefreshControl, Modal, Pressable, KeyboardAvoidingView, Platform, Alert } from "react-native";
import { useLocalSearchParams, useFocusEffect, Stack, router } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  Receipt,
  ArrowLeftRight,
  X,
  Plus,
  Trash2,
} from "lucide-react-native";
import { expensesAPI, settlementsAPI, groupsAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { SegmentedTabs } from "~/components/ui/tabs";

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

const SPLIT_METHODS = ["equal", "ratio", "exact", "shares"] as const;

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

  const handleDeleteGroup = () => {
    Alert.alert(t("delete_group"), t("delete_group_confirm"), [
      { text: t("cancel"), style: "cancel" },
      {
        text: t("delete"),
        style: "destructive",
        onPress: async () => {
          try {
            await groupsAPI.delete(id!);
            router.replace("/(tabs)");
          } catch (e: any) {
            const msg = e.response?.data?.detail || e.message || "Unknown error";
            Alert.alert(t("error"), msg);
          }
        },
      },
    ]);
  };

  const handleAddExpense = async () => {
    if (!desc || !amount || Number(amount) <= 0 || !id || !user) return;
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
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || "Unknown error";
      Alert.alert(t("error"), msg);
    } finally {
      setAdding(false);
    }
  };

  const renderExpense = ({ item }: { item: ExpenseItem }) => (
    <Card className="mb-3">
      <CardContent className="flex-row items-center p-4 gap-3">
        <View className="h-10 w-10 rounded-full bg-muted items-center justify-center">
          <Receipt size={20} color="hsl(240 3.8% 46.1%)" />
        </View>
        <View className="flex-1">
          <Text className="font-medium">{item.description}</Text>
          <Muted>
            {item.payer_display_name} {t("paid_by")}
          </Muted>
        </View>
        <View className="items-end gap-1">
          <Text className="text-lg font-bold text-primary">
            {item.currency} {parseFloat(item.total_amount).toLocaleString()}
          </Text>
          <Badge variant="secondary">{t(item.split_method)}</Badge>
        </View>
      </CardContent>
    </Card>
  );

  const renderSuggestion = ({ item }: { item: Suggestion }) => (
    <Card className="mb-3">
      <CardContent className="flex-row items-center justify-between p-4">
        <View className="flex-1">
          <Text>
            <Text className="font-bold text-destructive">
              {item.from_user_name}
            </Text>
            {"  "}
            {t("owes")}
            {"  "}
            <Text className="font-bold text-income">
              {item.to_user_name}
            </Text>
          </Text>
        </View>
        <Text className="text-lg font-bold text-primary">
          {item.currency} {parseFloat(item.amount).toLocaleString()}
        </Text>
      </CardContent>
    </Card>
  );

  return (
    <View className="flex-1 bg-background">
      <Stack.Screen
        options={{
          headerRight: () => (
            <Pressable onPress={handleDeleteGroup} className="pr-2">
              <Trash2 size={20} color="hsl(0 84.2% 60.2%)" />
            </Pressable>
          ),
        }}
      />
      <SegmentedTabs
        tabs={[
          { value: "expenses", label: t("expenses") },
          { value: "settlements", label: t("settlements") },
        ]}
        value={tab}
        onValueChange={(v) => setTab(v as Tab)}
        className="mx-5 mt-4"
      />

      {tab === "expenses" ? (
        <FlatList
          data={expenses}
          keyExtractor={(item) => item.id}
          renderItem={renderExpense}
          contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <EmptyState
              icon={Receipt}
              title={t("add_expense")}
              description={t("no_expenses_hint")}
              actionLabel={t("add_expense")}
              onAction={() => setShowAdd(true)}
            />
          }
        />
      ) : (
        <FlatList
          data={suggestions}
          keyExtractor={(item) => `${item.from_user_id}-${item.to_user_id}`}
          renderItem={renderSuggestion}
          contentContainerStyle={{ padding: 20 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <EmptyState
              icon={ArrowLeftRight}
              title={t("balanced")}
              description={t("all_balanced_hint")}
            />
          }
        />
      )}

      {tab === "expenses" && <FAB onPress={() => setShowAdd(true)} />}

      {/* Add Expense Bottom Sheet */}
      <Modal
        visible={showAdd}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAdd(false)}
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
                <H3>{t("add_expense")}</H3>
                <Pressable onPress={() => setShowAdd(false)}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              <View className="gap-4">
                <Input
                  label={t("description")}
                  value={desc}
                  onChangeText={setDesc}
                  placeholder={t("description")}
                />
                <Input
                  label={t("amount")}
                  value={amount}
                  onChangeText={(text) => {
                    if (text === "" || /^\d*\.?\d{0,2}$/.test(text)) {
                      setAmount(text);
                    }
                  }}
                  keyboardType="decimal-pad"
                  placeholder="0"
                />

                <View className="gap-2">
                  <Text className="text-sm font-medium">{t("split_method")}</Text>
                  <SegmentedTabs
                    tabs={SPLIT_METHODS.map((m) => ({
                      value: m,
                      label: t(m),
                    }))}
                    value={splitMethod}
                    onValueChange={setSplitMethod}
                  />
                </View>

                <Button
                  onPress={handleAddExpense}
                  loading={adding}
                  disabled={adding || !desc || !amount || Number(amount) <= 0}
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
