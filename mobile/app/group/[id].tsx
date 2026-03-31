import { useCallback, useState } from "react";
import { View, FlatList, RefreshControl, Modal, Pressable, KeyboardAvoidingView, Platform, Alert, ScrollView } from "react-native";
import { useLocalSearchParams, useFocusEffect, router } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  Receipt,
  ArrowLeftRight,
  X,
  Users,
  UserMinus,
} from "lucide-react-native";
import { expensesAPI, settlementsAPI, groupsAPI, authAPI, ExpenseSplitInput } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { SegmentedTabs } from "~/components/ui/tabs";

type Tab = "expenses" | "settlements" | "members";

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

interface Member {
  user: { id: string; display_name: string; email: string };
  role: string;
  joined_at: string;
}

const SPLIT_METHODS = ["equal", "ratio", "exact", "shares"] as const;

export default function GroupDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  const [tab, setTab] = useState<Tab>("expenses");
  const [expenses, setExpenses] = useState<ExpenseItem[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Add expense modal
  const [groupCurrency, setGroupCurrency] = useState("TWD");
  const [showAdd, setShowAdd] = useState(false);
  const [desc, setDesc] = useState("");
  const [amount, setAmount] = useState("");
  const [splitMethod, setSplitMethod] = useState<(typeof SPLIT_METHODS)[number]>("equal");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");
  const [splitInputs, setSplitInputs] = useState<Record<string, string>>({});

  // Add member modal
  const [showAddMember, setShowAddMember] = useState(false);
  const [memberEmail, setMemberEmail] = useState("");
  const [foundUser, setFoundUser] = useState<{ id: string; display_name: string; email: string } | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [addingMember, setAddingMember] = useState(false);
  const [lookupError, setLookupError] = useState("");

  const isAdmin = members.find((m) => m.user.id === user?.id)?.role === "admin";

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      const [expRes, sugRes, groupRes] = await Promise.all([
        expensesAPI.list(id),
        settlementsAPI.suggestions(id),
        groupsAPI.get(id),
      ]);
      setExpenses(expRes.data);
      setSuggestions(sugRes.data);
      setMembers(groupRes.data.members ?? []);
      if (groupRes.data.default_currency) {
        setGroupCurrency(groupRes.data.default_currency);
      }
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

  const initSplitInputs = (method: (typeof SPLIT_METHODS)[number]) => {
    const defaults: Record<string, string> = {};
    members.forEach((m) => {
      defaults[m.user.id] = method === "shares" || method === "ratio" ? "1" : "";
    });
    setSplitInputs(defaults);
  };

  const canSubmitExpense = (() => {
    if (!desc || !amount || Number(amount) <= 0) return false;
    if (splitMethod === "exact") {
      const sum = Object.values(splitInputs).reduce((acc, v) => acc + (Number(v) || 0), 0);
      return Math.abs(sum - Number(amount)) < 0.01;
    }
    if (splitMethod === "ratio" || splitMethod === "shares") {
      return Object.values(splitInputs).reduce((acc, v) => acc + (Number(v) || 0), 0) > 0;
    }
    return true;
  })();

  const handleAddExpense = async () => {
    setAddError("");
    if (!desc || !amount || Number(amount) <= 0 || !id || !user) return;

    let splits: ExpenseSplitInput[] | undefined;

    if (splitMethod === "exact") {
      splits = members.map((m) => ({
        user_id: m.user.id,
        amount: Number(splitInputs[m.user.id]) || 0,
      }));
      const sum = splits.reduce((acc, s) => acc + (s.amount ?? 0), 0);
      if (Math.abs(sum - Number(amount)) > 0.01) {
        setAddError(t("split_amounts_must_match"));
        return;
      }
    } else if (splitMethod === "ratio" || splitMethod === "shares") {
      const totalShares = Object.values(splitInputs).reduce((acc, v) => acc + (Number(v) || 0), 0);
      if (totalShares <= 0) {
        setAddError(t("need_positive_shares"));
        return;
      }
      splits = members.map((m) => ({
        user_id: m.user.id,
        shares: Number(splitInputs[m.user.id]) || 0,
      }));
    }

    setAdding(true);
    try {
      await expensesAPI.create(id, {
        description: desc,
        total_amount: parseFloat(amount),
        currency: groupCurrency,
        paid_by: user.id,
        split_method: splitMethod,
        splits,
      });
      setShowAdd(false);
      setDesc("");
      setAmount("");
      setSplitMethod("equal");
      setSplitInputs({});
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setAddError(msg);
    } finally {
      setAdding(false);
    }
  };

  const handleLookupUser = async () => {
    if (!memberEmail.trim()) return;
    setLookingUp(true);
    setFoundUser(null);
    setLookupError("");
    try {
      const res = await authAPI.lookupByEmail(memberEmail.trim());
      setFoundUser(res.data);
    } catch (e: any) {
      setLookupError(t("user_not_found"));
    } finally {
      setLookingUp(false);
    }
  };

  const handleAddMember = async () => {
    if (!foundUser || !id) return;
    setAddingMember(true);
    try {
      await groupsAPI.addMember(id, foundUser.id);
      setShowAddMember(false);
      setMemberEmail("");
      setFoundUser(null);
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || "Unknown error";
      Alert.alert(t("error"), msg);
    } finally {
      setAddingMember(false);
    }
  };

  const handleRemoveMember = (member: Member) => {
    const isSelf = member.user.id === user?.id;
    const title = isSelf ? t("leave_group") : t("remove_member");
    const message = isSelf
      ? t("leave_group_confirm")
      : t("remove_member_confirm", { name: member.user.display_name });

    Alert.alert(title, message, [
      { text: t("cancel"), style: "cancel" },
      {
        text: isSelf ? t("leave_group") : t("delete"),
        style: "destructive",
        onPress: async () => {
          try {
            await groupsAPI.removeMember(id!, member.user.id);
            if (isSelf) {
              router.replace("/(tabs)");
            } else {
              await fetchData();
            }
          } catch (e: any) {
            const msg = e.response?.data?.detail || e.message || "Unknown error";
            Alert.alert(t("error"), msg);
          }
        },
      },
    ]);
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

  const renderMember = ({ item }: { item: Member }) => {
    const isSelf = item.user.id === user?.id;
    const canRemove = isAdmin || isSelf;

    return (
      <Card className="mb-3">
        <CardContent className="flex-row items-center p-4 gap-3">
          <View className="h-10 w-10 rounded-full bg-muted items-center justify-center">
            <Users size={20} color="hsl(240 3.8% 46.1%)" />
          </View>
          <View className="flex-1">
            <Text className="font-medium">
              {item.user.display_name}
              {isSelf ? "  （你）" : ""}
            </Text>
            <Muted>{item.user.email}</Muted>
          </View>
          <View className="flex-row items-center gap-2">
            <Badge variant={item.role === "admin" ? "default" : "secondary"}>
              {t(item.role === "admin" ? "role_admin" : "role_member")}
            </Badge>
            {canRemove && (
              <Pressable onPress={() => handleRemoveMember(item)} className="p-1">
                <UserMinus size={18} color="hsl(0 84.2% 60.2%)" />
              </Pressable>
            )}
          </View>
        </CardContent>
      </Card>
    );
  };

  return (
    <View className="flex-1 bg-background">
      <SegmentedTabs
        tabs={[
          { value: "expenses", label: t("expenses") },
          { value: "settlements", label: t("settlements") },
          { value: "members", label: t("members") },
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
              onAction={() => { setAddError(""); setSplitMethod("equal"); setSplitInputs({}); setShowAdd(true); }}
            />
          }
        />
      ) : tab === "settlements" ? (
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
      ) : (
        <FlatList
          data={members}
          keyExtractor={(item) => item.user.id}
          renderItem={renderMember}
          contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <EmptyState
              icon={Users}
              title={t("members")}
              description={t("no_members_hint")}
            />
          }
        />
      )}

      {tab === "expenses" && <FAB onPress={() => { setAddError(""); setSplitMethod("equal"); setSplitInputs({}); setShowAdd(true); }} />}
      {tab === "members" && (
        <FAB onPress={() => { setShowAddMember(true); setMemberEmail(""); setFoundUser(null); setLookupError(""); }} />
      )}

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
                    onValueChange={(v) => {
                      const method = v as (typeof SPLIT_METHODS)[number];
                      setSplitMethod(method);
                      if (method !== "equal") {
                        initSplitInputs(method);
                      } else {
                        setSplitInputs({});
                      }
                    }}
                  />
                </View>

                {splitMethod !== "equal" && members.length > 0 && (
                  <View className="gap-3">
                    <Text className="text-sm font-medium">{t("split_details")}</Text>
                    <ScrollView style={{ maxHeight: 200 }} showsVerticalScrollIndicator={false}>
                      {members.map((m) => (
                        <View key={m.user.id} className="flex-row items-center gap-2 mb-2">
                          <Text className="flex-1 text-sm" numberOfLines={1}>
                            {m.user.display_name}
                          </Text>
                          <View className="w-28">
                            <Input
                              value={splitInputs[m.user.id] ?? ""}
                              onChangeText={(text) => {
                                if (text === "" || /^\d*\.?\d{0,2}$/.test(text)) {
                                  setSplitInputs((prev) => ({ ...prev, [m.user.id]: text }));
                                }
                              }}
                              keyboardType="decimal-pad"
                              placeholder={splitMethod === "exact" ? "0.00" : "1"}
                            />
                          </View>
                        </View>
                      ))}
                    </ScrollView>

                    {splitMethod === "exact" && amount ? (
                      (() => {
                        const total = Number(amount);
                        const sum = Object.values(splitInputs).reduce((acc, v) => acc + (Number(v) || 0), 0);
                        const diff = total - sum;
                        const isBalanced = Math.abs(diff) < 0.01;
                        return (
                          <Text className={`text-sm font-medium ${isBalanced ? "text-primary" : "text-destructive"}`}>
                            {diff >= 0 ? t("remaining") : t("exceeded")}: {Math.abs(diff).toFixed(2)}
                          </Text>
                        );
                      })()
                    ) : (splitMethod === "ratio" || splitMethod === "shares") && amount ? (
                      (() => {
                        const total = Number(amount);
                        const totalShares = Object.values(splitInputs).reduce((acc, v) => acc + (Number(v) || 0), 0);
                        return (
                          <View className="gap-1">
                            <Text className="text-sm text-muted-foreground">
                              {t("total_shares_label")}: {totalShares}
                            </Text>
                            {totalShares > 0 && members.map((m) => {
                              const s = Number(splitInputs[m.user.id]) || 0;
                              const est = (total * s / totalShares).toFixed(2);
                              return (
                                <Text key={m.user.id} className="text-xs text-muted-foreground">
                                  {m.user.display_name}: {groupCurrency} {est}
                                </Text>
                              );
                            })}
                          </View>
                        );
                      })()
                    ) : null}
                  </View>
                )}

                {addError ? (
                  <Text className="text-sm text-destructive">{addError}</Text>
                ) : null}

                <Button
                  onPress={handleAddExpense}
                  loading={adding}
                  disabled={adding || !canSubmitExpense}
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

      {/* Add Member Bottom Sheet */}
      <Modal
        visible={showAddMember}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAddMember(false)}
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
                <H3>{t("add_member_by_email")}</H3>
                <Pressable onPress={() => setShowAddMember(false)}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              <View className="gap-4">
                <View className="flex-row gap-2 items-end">
                  <View className="flex-1">
                    <Input
                      label={t("email")}
                      value={memberEmail}
                      onChangeText={(text) => {
                        setMemberEmail(text);
                        setFoundUser(null);
                        setLookupError("");
                      }}
                      placeholder={t("enter_email_to_add")}
                      keyboardType="email-address"
                      autoCapitalize="none"
                    />
                  </View>
                  <Button
                    onPress={handleLookupUser}
                    loading={lookingUp}
                    disabled={lookingUp || !memberEmail.trim()}
                    variant="outline"
                    className="mb-0.5"
                  >
                    {t("lookup")}
                  </Button>
                </View>

                {lookupError ? (
                  <Text className="text-destructive text-sm">{lookupError}</Text>
                ) : null}

                {foundUser && (
                  <Card>
                    <CardContent className="flex-row items-center p-4 gap-3">
                      <View className="h-10 w-10 rounded-full bg-muted items-center justify-center">
                        <Users size={20} color="hsl(240 3.8% 46.1%)" />
                      </View>
                      <View className="flex-1">
                        <Text className="font-medium">{foundUser.display_name}</Text>
                        <Muted>{foundUser.email}</Muted>
                      </View>
                    </CardContent>
                  </Card>
                )}

                <Button
                  onPress={handleAddMember}
                  loading={addingMember}
                  disabled={addingMember || !foundUser}
                  size="lg"
                  className="mt-2"
                >
                  {t("add_member")}
                </Button>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
