import { useCallback, useState, useRef, useEffect } from "react";
import { View, FlatList, RefreshControl, Modal, Pressable, KeyboardAvoidingView, Platform, Alert, ScrollView, ActivityIndicator, Image } from "react-native";
import { useLocalSearchParams, useFocusEffect, router } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  Receipt,
  ArrowsLeftRight,
  X,
  UsersThree,
  UserMinus,
  Check,
  CaretLeft,
  PencilSimple,
  Link,
  UserPlus,
  GearSix,
  CaretDown,
  CaretRight,
  Megaphone,
} from "phosphor-react-native";
import { CurrencyPicker } from "~/components/ui/currency-picker";
import { expensesAPI, settlementsAPI, groupsAPI, authAPI, exchangeRatesAPI, friendsAPI, ExpenseSplitInput, ExpensePayerInput, ExpenseUpdatePayload } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { useDraftStore } from "../../stores/draft";
import { addNotificationReceivedCallback } from "~/lib/notifications";
import { DiscardDraftDialog } from "~/components/ui/discard-draft-dialog";
import { Card, CardContent } from "~/components/ui/card";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { FAB } from "~/components/ui/fab";
import { EmptyState } from "~/components/ui/empty-state";
import { SegmentedTabs } from "~/components/ui/tabs";
import { useThemeClassName } from "~/lib/theme";
import { InviteShareModal } from "~/components/InviteShareModal";
import { CoverImagePicker } from "~/components/ui/cover-image-picker";

type Tab = "expenses" | "balances" | "members";

interface ExpenseSplitItem {
  user_id: string;
  user_display_name: string;
  amount: string;
  shares: string | null;
}

interface ExpensePayerItem {
  user_id: string;
  user_display_name: string;
  amount: string;
}

interface SettledInfo {
  settled_by: string;
  settled_at: string;
}

interface ExpenseItem {
  id: string;
  description: string;
  total_amount: string;
  currency: string;
  base_currency: string;
  base_amount: string;
  paid_by: string;
  payer_display_name: string;
  payers: ExpensePayerItem[];
  split_method: string;
  splits: ExpenseSplitItem[];
  note: string | null;
  expense_date: string | null;
  created_at: string;
  is_settled: boolean;
  settled_info: SettledInfo | null;
}

interface Suggestion {
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
  amount: string;
  currency: string;
}

interface PendingSettlement {
  id: string;
  from_user: string;
  from_user_name: string;
  to_user: string;
  to_user_name: string;
  amount: number;
  currency: string;
  status: string;
  settled_at: string;
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
  const themeClass = useThemeClassName();

  const [tab, setTab] = useState<Tab>("expenses");
  const [batchReminding, setBatchReminding] = useState(false);
  const [expenses, setExpenses] = useState<ExpenseItem[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [groupName, setGroupName] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  // Add expense modal
  const [groupCurrency, setGroupCurrency] = useState("TWD");
  const [showAdd, setShowAdd] = useState(false);
  const [desc, setDesc] = useState("");
  const [amount, setAmount] = useState("");
  const [splitMethod, setSplitMethod] = useState<(typeof SPLIT_METHODS)[number]>("equal");
  const [expenseCurrency, setExpenseCurrency] = useState("TWD");
  const [selectedMembers, setSelectedMembers] = useState<Set<string>>(new Set());
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");
  const [splitInputs, setSplitInputs] = useState<Record<string, string>>({});
  const [editingExpenseId, setEditingExpenseId] = useState<string | null>(null);
  const [editingSettled, setEditingSettled] = useState(false);
  const [convertedHint, setConvertedHint] = useState("");
  const [multiPayer, setMultiPayer] = useState(false);
  const [payerInputs, setPayerInputs] = useState<Record<string, string>>({});
  // Balance & settlement
  const [settleTarget, setSettleTarget] = useState<Suggestion | null>(null);
  const [settling, setSettling] = useState(false);
  const [settleError, setSettleError] = useState("");
  const [settleCurrency, setSettleCurrency] = useState("");
  const [settleAmount, setSettleAmount] = useState("");
  const [settleRate, setSettleRate] = useState<number | null>(null);
  const [converting, setConverting] = useState(false);
  const [pendingSettlements, setPendingSettlements] = useState<PendingSettlement[]>([]);
  const [settleSuccessMsg, setSettleSuccessMsg] = useState("");
  const [forgiveTarget, setForgiveTarget] = useState<Suggestion | null>(null);
  const [forgiving, setForgiving] = useState(false);
  const [forgiveError, setForgiveError] = useState("");

  // Unified currency settlement
  const [unifiedSettleTarget, setUnifiedSettleTarget] = useState<{ personId: string; personName: string; items: Suggestion[] } | null>(null);
  const [unifiedSettleCurrency, setUnifiedSettleCurrency] = useState("");
  const [unifiedSettleItems, setUnifiedSettleItems] = useState<{ currency: string; originalAmount: string; convertedAmount: number; rate: number | null }[]>([]);
  const [unifiedSettling, setUnifiedSettling] = useState(false);
  const [unifiedSettleError, setUnifiedSettleError] = useState("");
  const [unifiedConverting, setUnifiedConverting] = useState(false);

  // Balance summary collapse
  const [balanceSummaryExpanded, setBalanceSummaryExpanded] = useState(false);

  // Add member modal
  const [showAddMember, setShowAddMember] = useState(false);
  const [memberEmail, setMemberEmail] = useState("");
  const [foundUser, setFoundUser] = useState<{ id: string; display_name: string; email: string } | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [addingMember, setAddingMember] = useState(false);
  const [lookupError, setLookupError] = useState("");
  const [showInvite, setShowInvite] = useState(false);

  // Friend selection for add member
  type FriendItem = { id: string; display_name: string; email: string; friendship_id: string };
  const [friendsForAdd, setFriendsForAdd] = useState<FriendItem[]>([]);
  const [friendsLoading, setFriendsLoading] = useState(false);
  const [addingFriendId, setAddingFriendId] = useState<string | null>(null);

  // Friend status for members tab
  const [friendIdSet, setFriendIdSet] = useState<Set<string>>(new Set());
  const [sentRequestToIds, setSentRequestToIds] = useState<Set<string>>(new Set());
  const [sendingFriendRequestId, setSendingFriendRequestId] = useState<string | null>(null);

  // Email invitation
  const [inviteEmail, setInviteEmail] = useState("");
  const [sendingInvite, setSendingInvite] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [emailInvitations, setEmailInvitations] = useState<{ id: string; email: string; status: string; inviter_name: string; created_at: string; expires_at: string }[]>([]);

  // Group settings modal
  const [showSettings, setShowSettings] = useState(false);
  const [editGroupName, setEditGroupName] = useState("");
  const [editGroupCurrency, setEditGroupCurrency] = useState("TWD");
  const [editCoverUrl, setEditCoverUrl] = useState("");
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(null);

  // Pairwise debt details
  const [pairwiseDetails, setPairwiseDetails] = useState<Suggestion[]>([]);
  const [showDetails, setShowDetails] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [sugLoading, setSugLoading] = useState(false);
  const [showNotInvolved, setShowNotInvolved] = useState(false);
  const [showSettled, setShowSettled] = useState(false);
  const hasFetched = useRef(false);

  const isAdmin = members.find((m) => m.user.id === user?.id)?.role === "admin";

  // --- Draft / discard logic for expense modal ---
  const { saveDraft, getDraft, clearDraft } = useDraftStore();
  const EXPENSE_DRAFT_KEY = `expense-${id}`;
  const [showExpenseDiscardConfirm, setShowExpenseDiscardConfirm] = useState(false);

  const isExpenseDirty = !!(desc || amount) && !editingExpenseId;

  const resetExpenseForm = () => {
    setDesc("");
    setAmount("");
    setSplitMethod("equal");
    setSplitInputs({});
    setMultiPayer(false);
    setPayerInputs({});
    setAddError("");
    setEditingExpenseId(null);
    setEditingSettled(false);
  };

  const handleOpenAddExpense = () => {
    if (!editingExpenseId) {
      const draft = getDraft(EXPENSE_DRAFT_KEY);
      if (draft) {
        setDesc((draft.desc as string) || "");
        setAmount((draft.amount as string) || "");
        if (draft.expenseCurrency) setExpenseCurrency(draft.expenseCurrency as string);
        if (draft.splitMethod) setSplitMethod(draft.splitMethod as (typeof SPLIT_METHODS)[number]);
      }
    }
    setShowAdd(true);
  };

  const handleCloseExpenseModal = () => {
    if (isExpenseDirty) {
      setShowExpenseDiscardConfirm(true);
    } else {
      resetExpenseForm();
      setShowAdd(false);
    }
  };

  const handleDiscardExpense = () => {
    saveDraft(EXPENSE_DRAFT_KEY, { desc, amount, expenseCurrency, splitMethod });
    setShowExpenseDiscardConfirm(false);
    resetExpenseForm();
    setShowAdd(false);
  };

  const fetchFriendIds = useCallback(async () => {
    try {
      const res = await friendsAPI.list();
      const ids = new Set((res.data as any[]).map((f) => f.friend.id));
      setFriendIdSet(ids);
    } catch {
      // silently fail
    }
  }, []);

  const fetchEmailInvitations = useCallback(async () => {
    if (!id) return;
    try {
      const res = await groupsAPI.listEmailInvitations(id);
      setEmailInvitations(res.data);
    } catch {
      // silently fail
    }
  }, [id]);

  const refreshSettlements = useCallback(async () => {
    if (!id) return;
    setSugLoading(true);
    try {
      const [sugRes, settleRes] = await Promise.all([
        settlementsAPI.suggestions(id),
        settlementsAPI.list(id),
      ]);
      const data = sugRes.data;
      if (data.mode === "by_currency" && data.by_currency) {
        const flat = data.by_currency.flatMap((g: { suggestions: Suggestion[] }) => g.suggestions);
        setSuggestions(flat);
      } else if (data.mode === "unified" && data.unified) {
        setSuggestions(data.unified.suggestions);
      } else {
        setSuggestions([]);
      }
      const pending = (settleRes.data as PendingSettlement[]).filter((s) => s.status === "pending");
      setPendingSettlements(pending);
    } catch (e) {
      console.error("Failed to fetch suggestions", e);
    } finally {
      setSugLoading(false);
    }
  }, [id]);

  const fetchData = useCallback(async () => {
    if (!id) return;
    const isFirstLoad = !hasFetched.current;
    if (isFirstLoad) setLoading(true);
    try {
      // Phase 1: group info + expenses (fast) -- render immediately
      const [expRes, groupRes] = await Promise.all([
        expensesAPI.list(id),
        groupsAPI.get(id),
      ]);
      setExpenses(expRes.data);
      const rawMembers = groupRes.data.members ?? [];
      const sorted = [...rawMembers].sort((a, b) => {
        if (a.user.id === user?.id) return -1;
        if (b.user.id === user?.id) return 1;
        return 0;
      });
      setMembers(sorted);
      if (groupRes.data.name) setGroupName(groupRes.data.name);
      if (groupRes.data.default_currency) setGroupCurrency(groupRes.data.default_currency);
      if (groupRes.data.cover_image_url) setCoverImageUrl(groupRes.data.cover_image_url);
      hasFetched.current = true;
      if (isFirstLoad) setLoading(false);

      // Phase 2: settlement suggestions + email invitations + friend status -- load in background
      fetchEmailInvitations();
      refreshSettlements();
      fetchFriendIds();
    } catch (e) {
      console.error("Failed to fetch group data", e);
      if (isFirstLoad) setLoading(false);
    }
  }, [id, fetchEmailInvitations, refreshSettlements, fetchFriendIds]);

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [fetchData])
  );

  // 收到推播時即時刷新群組資料（餘額、結清、消費）
  useEffect(() => {
    return addNotificationReceivedCallback(() => {
      fetchData();
    });
  }, [fetchData]);

  // Debounced preferred currency conversion hint
  const preferredCurrency = user?.preferred_currency ?? "TWD";
  useEffect(() => {
    if (!amount || Number(amount) <= 0 || expenseCurrency === preferredCurrency) {
      setConvertedHint("");
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await exchangeRatesAPI.convert({
          from_currency: expenseCurrency,
          to_currency: preferredCurrency,
          amount: Number(amount),
        });
        const converted = Number(res.data.converted_amount);
        setConvertedHint(
          t("approx_preferred", {
            currency: preferredCurrency,
            amount: converted.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
          })
        );
      } catch {
        setConvertedHint("");
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [amount, expenseCurrency, preferredCurrency, t]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const selectedMembersList = members.filter((m) => selectedMembers.has(m.user.id));

  const toggleMember = (memberId: string) => {
    setSelectedMembers((prev) => {
      const next = new Set(prev);
      if (next.has(memberId)) {
        next.delete(memberId);
      } else {
        next.add(memberId);
      }
      return next;
    });
  };

  const toggleAllMembers = () => {
    if (selectedMembers.size === members.length) {
      setSelectedMembers(new Set());
    } else {
      setSelectedMembers(new Set(members.map((m) => m.user.id)));
    }
  };

  const initSplitInputs = (method: (typeof SPLIT_METHODS)[number]) => {
    const defaults: Record<string, string> = {};
    if (method === "ratio") {
      const n = selectedMembersList.length;
      const per = n > 0 ? (100 / n).toFixed(2) : "0";
      selectedMembersList.forEach((m) => {
        defaults[m.user.id] = per;
      });
    } else if (method === "shares") {
      selectedMembersList.forEach((m) => {
        defaults[m.user.id] = "1";
      });
    }
    setSplitInputs(defaults);
  };

  const canSubmitExpense = (() => {
    if (!desc || !amount || Number(amount) <= 0) return false;
    if (selectedMembers.size === 0) return false;
    if (splitMethod === "exact") {
      const sum = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
      return Math.abs(sum - Number(amount)) < 0.01;
    }
    if (splitMethod === "ratio") {
      const sum = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
      return Math.abs(sum - 100) < 0.01;
    }
    if (splitMethod === "shares") {
      return selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0) > 0;
    }
    return true;
  })();

  const openEditModal = (expense: ExpenseItem) => {
    setEditingExpenseId(expense.id);
    setEditingSettled(!!expense.is_settled);
    setDesc(expense.description);
    setAmount(parseFloat(expense.total_amount).toString());
    setExpenseCurrency(expense.currency);

    const method = expense.split_method as (typeof SPLIT_METHODS)[number];
    setSplitMethod(method);

    const splitMemberIds = new Set(expense.splits.map((s) => s.user_id));
    setSelectedMembers(splitMemberIds);

    if (method !== "equal") {
      const inputs: Record<string, string> = {};
      if (method === "exact") {
        expense.splits.forEach((s) => {
          inputs[s.user_id] = parseFloat(s.amount).toString();
        });
      } else if (method === "ratio") {
        const totalShares = expense.splits.reduce((acc, s) => acc + (s.shares ? parseFloat(s.shares) : 0), 0);
        expense.splits.forEach((s) => {
          const share = s.shares ? parseFloat(s.shares) : 0;
          const pct = totalShares > 0 ? ((share / totalShares) * 100).toFixed(2) : "0";
          inputs[s.user_id] = pct;
        });
      } else {
        expense.splits.forEach((s) => {
          inputs[s.user_id] = s.shares ? parseFloat(s.shares).toString() : "1";
        });
      }
      setSplitInputs(inputs);
    } else {
      setSplitInputs({});
    }

    // 載入多人付款資料
    if (expense.payers && expense.payers.length > 0) {
      setMultiPayer(true);
      const pInputs: Record<string, string> = {};
      expense.payers.forEach((p) => {
        pInputs[p.user_id] = parseFloat(p.amount).toString();
      });
      setPayerInputs(pInputs);
    } else {
      setMultiPayer(false);
      setPayerInputs({});
    }

    setAddError("");
    setShowAdd(true);
  };

  const handleSettleCurrencyChange = async (newCurrency: string) => {
    if (!settleTarget) return;
    setSettleCurrency(newCurrency);

    if (newCurrency === settleTarget.currency) {
      setSettleAmount(settleTarget.amount);
      setSettleRate(null);
      return;
    }

    setConverting(true);
    setSettleError("");
    try {
      const res = await exchangeRatesAPI.convert({
        from_currency: settleTarget.currency,
        to_currency: newCurrency,
        amount: parseFloat(settleTarget.amount),
      });
      setSettleAmount(String(res.data.converted_amount));
      setSettleRate(res.data.rate);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setSettleError(msg);
      // 轉換失敗時回退到原幣別
      setSettleCurrency(settleTarget.currency);
      setSettleAmount(settleTarget.amount);
      setSettleRate(null);
    } finally {
      setConverting(false);
    }
  };

  const handleSettleUp = async (suggestion: Suggestion) => {
    if (!id || !user) return;
    setSettling(true);
    setSettleError("");
    try {
      const isCurrencyChanged = settleCurrency !== suggestion.currency;
      await settlementsAPI.create(id, {
        to_user: suggestion.to_user_id,
        amount: parseFloat(settleAmount),
        currency: settleCurrency,
        ...(isCurrencyChanged && settleRate != null
          ? {
              original_currency: suggestion.currency,
              original_amount: parseFloat(suggestion.amount),
              locked_rate: settleRate,
            }
          : {}),
      });
      setSettleTarget(null);
      setSettleSuccessMsg(t("settlement_pending_hint"));
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setSettleError(msg);
    } finally {
      setSettling(false);
    }
  };

  const handleForgive = async (suggestion: Suggestion) => {
    if (!id || !user) return;
    setForgiving(true);
    setForgiveError("");
    try {
      await settlementsAPI.forgive(id, {
        from_user: suggestion.from_user_id,
        amount: parseFloat(suggestion.amount),
        currency: suggestion.currency,
      });
      setForgiveTarget(null);
      setSettleSuccessMsg(t("settlement_forgiven_success"));
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setForgiveError(msg);
    } finally {
      setForgiving(false);
    }
  };

  // --- Unified currency settlement ---
  const handleOpenUnifiedSettle = async (personId: string, personName: string, items: Suggestion[], targetCurrency: string) => {
    setUnifiedSettleTarget({ personId, personName, items });
    setUnifiedSettleCurrency(targetCurrency);
    setUnifiedSettleError("");
    setUnifiedConverting(true);
    try {
      const converted = await Promise.all(
        items.map(async (item) => {
          if (item.currency === targetCurrency) {
            return {
              currency: item.currency,
              originalAmount: item.amount,
              convertedAmount: Math.round(parseFloat(item.amount)),
              rate: null,
            };
          }
          const res = await exchangeRatesAPI.convert({
            from_currency: item.currency,
            to_currency: targetCurrency,
            amount: parseFloat(item.amount),
          });
          return {
            currency: item.currency,
            originalAmount: item.amount,
            convertedAmount: Math.round(res.data.converted_amount),
            rate: res.data.rate,
          };
        })
      );
      setUnifiedSettleItems(converted);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setUnifiedSettleError(msg);
      setUnifiedSettleItems([]);
    } finally {
      setUnifiedConverting(false);
    }
  };

  const handleUnifiedSettleCurrencyChange = async (newCurrency: string) => {
    if (!unifiedSettleTarget) return;
    await handleOpenUnifiedSettle(
      unifiedSettleTarget.personId,
      unifiedSettleTarget.personName,
      unifiedSettleTarget.items,
      newCurrency,
    );
  };

  const handleUnifiedSettleConfirm = async () => {
    if (!id || !user || !unifiedSettleTarget || unifiedSettleItems.length === 0) return;
    setUnifiedSettling(true);
    setUnifiedSettleError("");
    try {
      for (const item of unifiedSettleItems) {
        const isCurrencyChanged = unifiedSettleCurrency !== item.currency;
        await settlementsAPI.create(id, {
          to_user: unifiedSettleTarget.personId,
          amount: item.convertedAmount,
          currency: unifiedSettleCurrency,
          ...(isCurrencyChanged && item.rate != null
            ? {
                original_currency: item.currency,
                original_amount: parseFloat(item.originalAmount),
                locked_rate: item.rate,
              }
            : {}),
        });
      }
      setUnifiedSettleTarget(null);
      setUnifiedSettleItems([]);
      setSettleSuccessMsg(t("settlement_pending_hint"));
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setUnifiedSettleError(msg);
    } finally {
      setUnifiedSettling(false);
    }
  };

  const handleSubmitExpense = async () => {
    setAddError("");
    if (!desc || !amount || Number(amount) <= 0 || !id || !user) return;
    if (selectedMembers.size === 0) {
      setAddError(t("at_least_one_participant"));
      return;
    }

    let splits: ExpenseSplitInput[] | undefined;

    if (splitMethod === "equal") {
      splits = selectedMembersList.map((m) => ({ user_id: m.user.id }));
    } else if (splitMethod === "exact") {
      splits = selectedMembersList.map((m) => ({
        user_id: m.user.id,
        amount: Number(splitInputs[m.user.id]) || 0,
      }));
      const sum = splits.reduce((acc, s) => acc + (s.amount ?? 0), 0);
      if (Math.abs(sum - Number(amount)) > 0.01) {
        setAddError(t("split_amounts_must_match"));
        return;
      }
    } else if (splitMethod === "ratio") {
      const totalPct = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
      if (Math.abs(totalPct - 100) > 0.01) {
        setAddError(t("ratio_must_equal_100"));
        return;
      }
      splits = selectedMembersList.map((m) => ({
        user_id: m.user.id,
        shares: Number(splitInputs[m.user.id]) || 0,
      }));
    } else if (splitMethod === "shares") {
      const totalShares = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
      if (totalShares <= 0) {
        setAddError(t("need_positive_shares"));
        return;
      }
      splits = selectedMembersList.map((m) => ({
        user_id: m.user.id,
        shares: Number(splitInputs[m.user.id]) || 0,
      }));
    }

    // 多人付款驗證
    let payersData: ExpensePayerInput[] | undefined;
    if (multiPayer) {
      const payerEntries = Object.entries(payerInputs).filter(([, v]) => Number(v) > 0);
      if (payerEntries.length === 0) {
        setAddError(t("payers_must_equal_total"));
        return;
      }
      const payerSum = payerEntries.reduce((acc, [, v]) => acc + Number(v), 0);
      if (Math.abs(payerSum - Number(amount)) > 0.01) {
        setAddError(t("payers_must_equal_total"));
        return;
      }
      payersData = payerEntries.map(([uid, v]) => ({ user_id: uid, amount: Number(v) }));
    }

    setAdding(true);
    try {
      if (editingExpenseId) {
        await expensesAPI.update(id, editingExpenseId, {
          description: desc,
          total_amount: parseFloat(amount),
          currency: expenseCurrency,
          split_method: splitMethod,
          splits,
          ...(multiPayer && payersData ? { payers: payersData } : {}),
        });
      } else {
        await expensesAPI.create(id, {
          description: desc,
          total_amount: parseFloat(amount),
          currency: expenseCurrency,
          paid_by: user.id,
          split_method: splitMethod,
          splits,
          ...(multiPayer && payersData ? { payers: payersData } : {}),
        });
      }
      clearDraft(EXPENSE_DRAFT_KEY);
      setShowAdd(false);
      resetExpenseForm();
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setAddError(msg);
    } finally {
      setAdding(false);
    }
  };

  const fetchFriendsForAdd = async () => {
    setFriendsLoading(true);
    try {
      const res = await friendsAPI.list();
      const memberIds = new Set(members.map((m) => m.user.id));
      const available = (res.data as any[])
        .filter((f) => !memberIds.has(f.friend.id))
        .map((f) => ({
          id: f.friend.id,
          display_name: f.friend.display_name,
          email: f.friend.email,
          friendship_id: f.friendship_id,
        }));
      setFriendsForAdd(available);
    } catch {
      setFriendsForAdd([]);
    } finally {
      setFriendsLoading(false);
    }
  };

  const handleAddFriendAsMember = async (friend: FriendItem) => {
    if (!id) return;
    setAddingFriendId(friend.id);
    try {
      await groupsAPI.addMember(id, friend.id);
      setFriendsForAdd((prev) => prev.filter((f) => f.id !== friend.id));
      await fetchData();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setLookupError(msg);
    } finally {
      setAddingFriendId(null);
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

  const handleSendEmailInvitation = async () => {
    if (!inviteEmail.trim() || !id) return;
    setSendingInvite(true);
    setInviteError("");
    setInviteSuccess("");
    try {
      await groupsAPI.sendEmailInvitation(id, inviteEmail.trim());
      setInviteSuccess(t("invitation_sent", { email: inviteEmail.trim() }));
      setInviteEmail("");
      fetchEmailInvitations();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || t("unknown_error");
      setInviteError(msg);
    } finally {
      setSendingInvite(false);
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

  const isUserInvolved = (item: ExpenseItem): boolean => {
    const uid = user?.id;
    if (!uid) return false;
    if (item.paid_by === uid) return true;
    if (item.payers?.some((p) => p.user_id === uid)) return true;
    if (item.splits?.some((s) => s.user_id === uid)) return true;
    return false;
  };

  const renderExpense = ({ item }: { item: ExpenseItem }) => {
    const settled = item.is_settled;
    return (
      <Pressable
        onPress={() => {
          openEditModal(item);
        }}
      >
        <Card className={`mb-3 ${settled ? "opacity-50" : ""}`}>
          <CardContent className="flex-row items-center p-4 gap-3">
            <View className={`h-10 w-10 rounded-full items-center justify-center ${settled ? "bg-muted/50" : "bg-muted"}`}>
              {settled ? (
                <Check size={20} color="hsl(142 71% 45%)" weight="bold" />
              ) : (
                <Receipt size={20} color="hsl(240 3.8% 46.1%)" />
              )}
            </View>
            <View className="flex-1">
              <Text className={`font-medium ${settled ? "line-through text-muted-foreground" : ""}`}>{item.description}</Text>
              <Muted>
                {item.payer_display_name} {t("paid_by")}
              </Muted>
            </View>
            <View className="items-end gap-1">
              <Text className={`text-lg font-bold ${settled ? "text-muted-foreground" : "text-primary"}`}>
                {item.currency} {parseFloat(item.total_amount).toLocaleString()}
              </Text>
              {item.currency !== item.base_currency && (
                <Muted className="text-xs">
                  {item.base_currency} {parseFloat(item.base_amount).toLocaleString()}
                </Muted>
              )}
              <View className="flex-row items-center gap-1.5">
                {item.payers && item.payers.length > 0 && (
                  <Badge variant="outline">{t("multiple_payers")}</Badge>
                )}
                <Badge variant="secondary">{t(item.split_method)}</Badge>
                {!settled && <PencilSimple size={14} color="hsl(240 3.8% 46.1%)" weight="regular" />}
              </View>
            </View>
          </CardContent>
        </Card>
      </Pressable>
    );
  };

  const hasPendingFor = (fromId: string, toId: string) =>
    pendingSettlements.some((s) => s.from_user === fromId && s.to_user === toId);

  const handleSendFriendRequest = async (member: Member) => {
    setSendingFriendRequestId(member.user.id);
    try {
      await friendsAPI.sendRequest(member.user.email);
      setSentRequestToIds((prev) => new Set(prev).add(member.user.id));
    } catch (e: any) {
      const msg = e?.response?.data?.detail;
      if (msg === "Already friends") {
        setFriendIdSet((prev) => new Set(prev).add(member.user.id));
      } else if (msg === "Friend request already pending") {
        setSentRequestToIds((prev) => new Set(prev).add(member.user.id));
      }
    } finally {
      setSendingFriendRequestId(null);
    }
  };

  const renderMember = ({ item }: { item: Member }) => {
    const isSelf = item.user.id === user?.id;
    const canRemove = isAdmin || isSelf;
    const isFriend = friendIdSet.has(item.user.id);
    const hasSentRequest = sentRequestToIds.has(item.user.id);
    const isSending = sendingFriendRequestId === item.user.id;

    return (
      <Card className="mb-3">
        <CardContent className="flex-row items-center p-4 gap-3">
          <View className="h-10 w-10 rounded-full bg-muted items-center justify-center">
            <UsersThree size={20} color="hsl(240 3.8% 46.1%)" weight="regular" />
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
            {!isSelf && !isFriend && (
              hasSentRequest ? (
                <Badge variant="outline">{t("request_sent")}</Badge>
              ) : (
                <Pressable
                  onPress={() => handleSendFriendRequest(item)}
                  disabled={isSending}
                  className="p-1"
                >
                  {isSending ? (
                    <ActivityIndicator size="small" />
                  ) : (
                    <UserPlus size={18} color="hsl(var(--primary))" />
                  )}
                </Pressable>
              )
            )}
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
      {/* Custom header with back button */}
      <View className="flex-row items-center px-3 pt-3 pb-1 gap-1">
        <Pressable
          onPress={() => router.canGoBack() ? router.back() : router.replace("/(tabs)")}
          className="flex-row items-center p-2 -ml-1"
        >
          <CaretLeft size={24} color="hsl(var(--primary))" weight="regular" />
          <Text className="text-primary text-base">{t("groups")}</Text>
        </Pressable>
        <Text className="flex-1 text-lg font-semibold text-foreground text-center" numberOfLines={1}>
          {groupName}
        </Text>
        <Pressable
          onPress={() => {
            setEditGroupName(groupName);
            setEditGroupCurrency(groupCurrency);
            setEditCoverUrl(coverImageUrl || "");
            setSettingsError(null);
            setShowSettings(true);
          }}
          className="p-2"
        >
          <GearSix size={22} color="hsl(var(--primary))" />
        </Pressable>
        <Pressable
          onPress={() => setShowInvite(true)}
          className="p-2 -mr-1"
        >
          <Link size={22} color="hsl(var(--primary))" />
        </Pressable>
      </View>

      {coverImageUrl ? (
        <View className="mx-5 mt-2 rounded-xl overflow-hidden" style={{ height: 120 }}>
          <Image
            source={{ uri: coverImageUrl }}
            style={{ width: "100%", height: "100%" }}
            resizeMode="cover"
          />
        </View>
      ) : null}

      {/* Balance summary above tabs — collapsible (Splitwise style) */}
      {(() => {
        const mySuggestions = suggestions.filter((s) => s.from_user_id === user?.id || s.to_user_id === user?.id);
        const owedToMe = mySuggestions.filter((s) => s.to_user_id === user?.id);
        const iOwe = mySuggestions.filter((s) => s.from_user_id === user?.id);
        // Group by currency for totals
        const owedByCurrency: Record<string, number> = {};
        owedToMe.forEach((s) => { owedByCurrency[s.currency] = (owedByCurrency[s.currency] || 0) + parseFloat(s.amount); });
        const oweByCurrency: Record<string, number> = {};
        iOwe.forEach((s) => { oweByCurrency[s.currency] = (oweByCurrency[s.currency] || 0) + parseFloat(s.amount); });
        const hasOwed = owedToMe.length > 0;
        const hasOwe = iOwe.length > 0;
        if (!hasOwed && !hasOwe) return null;
        return (
          <Pressable
            onPress={() => setBalanceSummaryExpanded((v) => !v)}
            className="mx-5 mt-3 mb-1"
          >
            {hasOwed && (
              <View className={balanceSummaryExpanded ? "mb-2" : ""}>
                <View className="flex-row items-center">
                  <Text className="text-base font-semibold text-income flex-1">
                    {Object.entries(owedByCurrency).map(([cur, amt]) =>
                      t("gets_back_total", { currency: cur, amount: amt.toLocaleString() })
                    ).join(" + ")}
                  </Text>
                  {!hasOwe && (
                    balanceSummaryExpanded
                      ? <CaretDown size={16} color="hsl(240 3.8% 46.1%)" />
                      : <CaretRight size={16} color="hsl(240 3.8% 46.1%)" />
                  )}
                </View>
                {balanceSummaryExpanded && owedToMe.map((s) => (
                  <Text key={`${s.from_user_id}-${s.to_user_id}`} className="text-sm text-muted-foreground ml-2 mt-0.5">
                    {t("owes_you", { name: s.from_user_name })} {s.currency} {parseFloat(s.amount).toLocaleString()}
                  </Text>
                ))}
              </View>
            )}
            {hasOwe && (
              <View className="mb-1">
                <View className="flex-row items-center">
                  <Text className="text-base font-semibold text-destructive flex-1">
                    {Object.entries(oweByCurrency).map(([cur, amt]) =>
                      t("owes_total", { currency: cur, amount: amt.toLocaleString() })
                    ).join(" + ")}
                  </Text>
                  {balanceSummaryExpanded
                    ? <CaretDown size={16} color="hsl(240 3.8% 46.1%)" />
                    : <CaretRight size={16} color="hsl(240 3.8% 46.1%)" />
                  }
                </View>
                {balanceSummaryExpanded && iOwe.map((s) => (
                  <Text key={`${s.from_user_id}-${s.to_user_id}`} className="text-sm text-muted-foreground ml-2 mt-0.5">
                    {t("you_owe_person", { name: s.to_user_name })} {s.currency} {parseFloat(s.amount).toLocaleString()}
                  </Text>
                ))}
              </View>
            )}
          </Pressable>
        );
      })()}

      <SegmentedTabs
        tabs={[
          { value: "expenses", label: t("expenses") },
          { value: "balances", label: t("balances") },
          { value: "members", label: t("members") },
        ]}
        value={tab}
        onValueChange={(v) => {
          setTab(v as Tab);
          if (v === "balances") {
            refreshSettlements();
          }
        }}
        className="mx-5 mt-4"
      />

      {loading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" />
        </View>
      ) : tab === "expenses" ? (
        (() => {
          const unsettled = expenses.filter((e) => !e.is_settled);
          const settled = expenses.filter((e) => e.is_settled);
          const myUnsettled = unsettled.filter((e) => isUserInvolved(e));
          const otherUnsettled = unsettled.filter((e) => !isUserInvolved(e));
          return (
            <FlatList
              data={myUnsettled}
              keyExtractor={(item) => item.id}
              renderItem={renderExpense}
              contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              ListEmptyComponent={
                otherUnsettled.length === 0 && settled.length === 0 ? (
                  <EmptyState
                    icon={Receipt}
                    title={t("add_expense")}
                    description={t("no_expenses_hint")}
                    actionLabel={t("add_expense")}
                    onAction={() => { resetExpenseForm(); setSelectedMembers(new Set(members.map((m) => m.user.id))); setExpenseCurrency(groupCurrency); handleOpenAddExpense(); }}
                  />
                ) : null
              }
              ListFooterComponent={
                <>
                  {otherUnsettled.length > 0 && (
                    <View className="mt-4">
                      <Pressable
                        onPress={() => setShowNotInvolved(!showNotInvolved)}
                        className="flex-row items-center justify-between py-3 px-1"
                      >
                        <Text className="text-sm font-medium text-muted-foreground">
                          {t("not_involved_expenses")} ({otherUnsettled.length})
                        </Text>
                        {showNotInvolved ? (
                          <CaretDown size={16} color="hsl(240 3.8% 46.1%)" />
                        ) : (
                          <CaretRight size={16} color="hsl(240 3.8% 46.1%)" />
                        )}
                      </Pressable>
                      {showNotInvolved && (
                        <View>
                          {otherUnsettled.map((item) => (
                            <View key={item.id}>{renderExpense({ item })}</View>
                          ))}
                        </View>
                      )}
                    </View>
                  )}
                  {settled.length > 0 && (
                    <View className="mt-4">
                      <Pressable
                        onPress={() => setShowSettled(!showSettled)}
                        className="flex-row items-center justify-between py-3 px-1"
                      >
                        <Text className="text-sm font-medium text-muted-foreground">
                          {t("settled_expenses")} ({settled.length})
                        </Text>
                        {showSettled ? (
                          <CaretDown size={16} color="hsl(240 3.8% 46.1%)" />
                        ) : (
                          <CaretRight size={16} color="hsl(240 3.8% 46.1%)" />
                        )}
                      </Pressable>
                      {showSettled && (
                        <View>
                          {settled.map((item) => (
                            <View key={item.id}>{renderExpense({ item })}</View>
                          ))}
                        </View>
                      )}
                    </View>
                  )}
                </>
              }
            />
          );
        })()
      ) : tab === "balances" ? (
        sugLoading && suggestions.length === 0 ? (
          <View className="flex-1 items-center justify-center">
            <ActivityIndicator size="large" />
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={{ padding: 20, paddingBottom: 100 }}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
          >
            {settleSuccessMsg ? (
              <View className="bg-primary/10 rounded-lg px-4 py-3 mb-4">
                <Text className="text-sm text-primary font-medium">{settleSuccessMsg}</Text>
              </View>
            ) : null}

            {/* Pending settlements */}
            {pendingSettlements.length > 0 && (
              <Card className="mb-4">
                <CardContent className="p-4 gap-2">
                  <Text className="font-semibold text-sm text-muted-foreground">{t("pending_settlements")}</Text>
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

            {(() => {
              const mySuggestions = suggestions.filter((s) => s.from_user_id === user?.id || s.to_user_id === user?.id);
              const owedToMe = mySuggestions.filter((s) => s.to_user_id === user?.id);
              const iOwe = mySuggestions.filter((s) => s.from_user_id === user?.id);

              if (mySuggestions.length === 0) {
                return (
                  <EmptyState
                    icon={ArrowsLeftRight}
                    title={t("balanced")}
                    description={t("all_balanced_hint")}
                  />
                );
              }

              return (
                <View className="gap-4">
                  {/* Section: Others owe me */}
                  {owedToMe.length > 0 && (
                    <Card>
                      <CardContent className="p-4 gap-3">
                        <View className="flex-row items-center justify-between">
                          <Text className="font-semibold text-income">{t("owed_to_you")}</Text>
                          {owedToMe.length > 1 && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={batchReminding}
                              onPress={async () => {
                                setBatchReminding(true);
                                try {
                                  const res = await settlementsAPI.sendBatchReminders(id!, {
                                    reminders: owedToMe.map((s) => ({
                                      to_user: s.from_user_id,
                                      amount: parseFloat(s.amount),
                                      currency: s.currency,
                                    })),
                                  });
                                  const sentCount = res.data.sent?.length || 0;
                                  const skippedCount = res.data.skipped?.length || 0;
                                  let msg = t("batch_remind_sent", { count: sentCount });
                                  if (skippedCount > 0) {
                                    msg += "\n" + t("batch_remind_skipped", { count: skippedCount });
                                  }
                                  setSettleSuccessMsg(msg);
                                } catch (e: any) {
                                  setAddError(e.response?.data?.detail || t("unknown_error"));
                                } finally {
                                  setBatchReminding(false);
                                }
                              }}
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
                            <View key={`${item.from_user_id}-${item.to_user_id}`} className="gap-2">
                              <View className="flex-row items-center justify-between">
                                <Text className="text-sm flex-1">
                                  {t("owes_you", { name: item.from_user_name })}
                                </Text>
                                <Text className="text-base font-bold text-income">
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
                                  onPress={async () => {
                                    try {
                                      await settlementsAPI.sendReminder(id!, {
                                        to_user: item.from_user_id,
                                        amount: parseFloat(item.amount),
                                        currency: item.currency,
                                      });
                                      setSettleSuccessMsg(t("reminder_sent"));
                                    } catch (e: any) {
                                      setAddError(e.response?.data?.detail || t("reminder_cooldown"));
                                    }
                                  }}
                                  className="flex-1"
                                >
                                  {t("remind")}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onPress={() => {
                                    setForgiveTarget(item);
                                    setForgiveError("");
                                  }}
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
                    // Group iOwe by to_user_id
                    const grouped = new Map<string, { name: string; items: Suggestion[] }>();
                    for (const item of iOwe) {
                      if (!grouped.has(item.to_user_id)) {
                        grouped.set(item.to_user_id, { name: item.to_user_name, items: [] });
                      }
                      grouped.get(item.to_user_id)!.items.push(item);
                    }
                    return (
                      <Card>
                        <CardContent className="p-4 gap-3">
                          <Text className="font-semibold text-destructive">{t("you_owe")}</Text>
                          {Array.from(grouped).map(([personId, { name, items }]) => {
                            const alreadyPending = hasPendingFor(items[0].from_user_id, personId);
                            const canSettle = items[0].from_user_id === user?.id;
                            const hasMultipleCurrencies = items.length > 1;
                            return (
                              <View key={personId} className="gap-2">
                                {/* Person header: name + unified settle button */}
                                <View className="flex-row items-center justify-between">
                                  <Text className="text-sm font-medium flex-1">
                                    {t("you_owe_person", { name })}
                                  </Text>
                                  {canSettle && hasMultipleCurrencies && (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      disabled={alreadyPending}
                                      onPress={() => {
                                        setSettleSuccessMsg("");
                                        handleOpenUnifiedSettle(personId, name, items, groupCurrency);
                                      }}
                                    >
                                      {t("unified_settle")}
                                    </Button>
                                  )}
                                </View>
                                {alreadyPending && (
                                  <Text className="text-xs text-warning pl-3">{t("settlement_pending_hint")}</Text>
                                )}
                                {/* Per-currency rows */}
                                {items.map((item) => (
                                  <View key={`${item.from_user_id}-${item.to_user_id}-${item.currency}`} className="flex-row items-center justify-between pl-3">
                                    <Text className="text-base font-bold text-destructive flex-1">
                                      {item.currency} {parseFloat(item.amount).toLocaleString()}
                                    </Text>
                                    {canSettle && (
                                      <Button
                                        size="sm"
                                        disabled={alreadyPending}
                                        onPress={() => {
                                          setSettleSuccessMsg("");
                                          setSettleTarget(item);
                                          setSettleCurrency(item.currency);
                                          setSettleAmount(item.amount);
                                          setSettleRate(null);
                                          setSettleError("");
                                        }}
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

                  {/* Section: All members balances */}
                  <Card>
                    <CardContent className="p-4 gap-2">
                      <Text className="font-semibold text-sm text-muted-foreground">{t("all_members_balances")}</Text>
                      {members.map((m) => {
                        // Calculate net balance for this member from all suggestions
                        const owedSum = suggestions
                          .filter((s) => s.to_user_id === m.user.id)
                          .reduce((sum, s) => sum + parseFloat(s.amount), 0);
                        const owesSum = suggestions
                          .filter((s) => s.from_user_id === m.user.id)
                          .reduce((sum, s) => sum + parseFloat(s.amount), 0);
                        const net = owedSum - owesSum;
                        const isSettled = Math.abs(net) < 0.01;
                        return (
                          <View key={m.user.id} className="flex-row items-center justify-between py-1.5">
                            <Text className={`text-sm ${isSettled ? "text-muted-foreground" : ""}`}>
                              {m.user.display_name}
                              {m.user.id === user?.id ? ` (${t("me")})` : ""}
                            </Text>
                            {isSettled ? (
                              <Text className="text-sm text-muted-foreground">{t("is_settled_up")}</Text>
                            ) : net > 0 ? (
                              <Text className="text-sm font-medium text-income">
                                +{groupCurrency} {net.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </Text>
                            ) : (
                              <Text className="text-sm font-medium text-destructive">
                                -{groupCurrency} {Math.abs(net).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </Text>
                            )}
                          </View>
                        );
                      })}
                    </CardContent>
                  </Card>

                  {/* Pairwise debt details (expandable) */}
                  {suggestions.length > 0 && (
                    <View className="mt-1 mb-4">
                      <Pressable
                        className="flex-row items-center gap-2 py-3 px-1"
                        onPress={async () => {
                          if (showDetails) {
                            setShowDetails(false);
                            return;
                          }
                          if (pairwiseDetails.length === 0) {
                            setDetailsLoading(true);
                            try {
                              const res = await settlementsAPI.pairwiseDetails(id!);
                              setPairwiseDetails(res.data);
                            } catch (e) {
                              console.error("Failed to fetch pairwise details", e);
                            } finally {
                              setDetailsLoading(false);
                            }
                          }
                          setShowDetails(true);
                        }}
                      >
                        {showDetails
                          ? <CaretDown size={18} color="hsl(240 3.8% 46.1%)" />
                          : <CaretRight size={18} color="hsl(240 3.8% 46.1%)" />}
                        <Text className="text-muted-foreground font-medium">
                          {showDetails ? t("hide_details") : t("show_details")}
                        </Text>
                        {detailsLoading && <ActivityIndicator size="small" />}
                      </Pressable>
                      {showDetails && pairwiseDetails.length > 0 && (
                        <View className="gap-2 mt-1">
                          <Muted className="text-xs px-1">{t("debt_details")}</Muted>
                          {pairwiseDetails.map((d, i) => (
                            <View key={i} className="flex-row items-center justify-between px-3 py-2 bg-muted/50 rounded-lg">
                              <Text className="text-sm flex-1">
                                {d.from_user_name} → {d.to_user_name}
                              </Text>
                              <Text className="text-sm font-medium">
                                {d.currency} {parseFloat(d.amount).toLocaleString()}
                              </Text>
                            </View>
                          ))}
                        </View>
                      )}
                    </View>
                  )}
                </View>
              );
            })()}
          </ScrollView>
        )
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
              icon={UsersThree}
              title={t("members")}
              description={t("no_members_hint")}
            />
          }
          ListFooterComponent={
            emailInvitations.filter((inv) => inv.status === "pending").length > 0 ? (
              <View className="mt-4">
                <Muted className="mb-2 text-sm font-medium">{t("pending_invitations")}</Muted>
                {emailInvitations
                  .filter((inv) => inv.status === "pending")
                  .map((inv) => (
                    <Card key={inv.id} className="mb-2">
                      <CardContent className="flex-row items-center p-4 gap-3">
                        <View className="h-10 w-10 rounded-full bg-muted items-center justify-center">
                          <UserPlus size={20} color="hsl(240 3.8% 46.1%)" weight="regular" />
                        </View>
                        <View className="flex-1">
                          <Text className="font-medium">{inv.email}</Text>
                          <Muted className="text-xs">
                            {t("invited_by", { name: inv.inviter_name })}
                          </Muted>
                        </View>
                        <Pressable
                          onPress={async () => {
                            if (!id) return;
                            try {
                              await groupsAPI.cancelEmailInvitation(id, inv.id);
                              fetchEmailInvitations();
                            } catch (e: any) {
                              const msg = e.response?.data?.detail || e.message || t("unknown_error");
                              Alert.alert(t("error"), msg);
                            }
                          }}
                          className="p-2"
                        >
                          <X size={18} color="hsl(0 84.2% 60.2%)" weight="bold" />
                        </Pressable>
                      </CardContent>
                    </Card>
                  ))}
              </View>
            ) : null
          }
        />
      )}

      {tab === "expenses" && <FAB label={t("add_expense")} onPress={() => { resetExpenseForm(); setSelectedMembers(new Set(members.map((m) => m.user.id))); setExpenseCurrency(groupCurrency); handleOpenAddExpense(); }} />}
      {tab === "members" && (
        <FAB label={t("add_member")} onPress={() => { setShowAddMember(true); setMemberEmail(""); setFoundUser(null); setLookupError(""); setInviteEmail(""); setInviteError(""); setInviteSuccess(""); }} />
      )}

      <InviteShareModal
        visible={showInvite}
        onClose={() => setShowInvite(false)}
        groupId={id!}
        groupName={groupName}
        isAdmin={isAdmin}
      />

      {/* Add Expense Bottom Sheet */}
      <Modal
        visible={showAdd}
        transparent
        animationType="slide"
        onRequestClose={handleCloseExpenseModal}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <Pressable className="flex-1" onPress={handleCloseExpenseModal} />
          <View className="bg-background rounded-t-2xl px-5 pb-10 pt-4">
            <View className="items-center mb-4">
              <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
            </View>

            <View className="flex-row items-center justify-between mb-6">
              <H3>{editingExpenseId ? t("edit_expense") : t("add_expense")}</H3>
              <Pressable onPress={handleCloseExpenseModal}>
                <X size={24} color="hsl(240 3.8% 46.1%)" />
              </Pressable>
            </View>

              {editingSettled && (
                <View className="mb-4 p-3 rounded-lg bg-warning/10 border border-warning/30">
                  <Text className="text-sm text-warning font-medium">{t("edit_settled_warning")}</Text>
                </View>
              )}

              <ScrollView showsVerticalScrollIndicator={false} style={{ maxHeight: 500 }}>
                <View className="gap-4">
                  <Input
                    label={t("description")}
                    value={desc}
                    onChangeText={setDesc}
                    placeholder={t("description")}
                  />

                  <View className="flex-row gap-3">
                    <View className="flex-1">
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
                    </View>
                    <View className="w-40">
                      <CurrencyPicker
                        label={t("currency")}
                        value={expenseCurrency}
                        onSelect={setExpenseCurrency}
                      />
                    </View>
                  </View>

                  {convertedHint ? (
                    <Text className="text-xs text-muted-foreground -mt-2">{convertedHint}</Text>
                  ) : null}

                  {/* Payer mode toggle */}
                  <View className="gap-2">
                    <Text className="text-sm font-medium">{t("payers")}</Text>
                    <SegmentedTabs
                      tabs={[
                        { value: "single", label: t("single_payer") },
                        { value: "multi", label: t("multiple_payers") },
                      ]}
                      value={multiPayer ? "multi" : "single"}
                      onValueChange={(v) => {
                        const isMulti = v === "multi";
                        setMultiPayer(isMulti);
                        if (isMulti && Object.keys(payerInputs).length === 0) {
                          // 預設當前使用者為付款人
                          setPayerInputs({ [user!.id]: amount || "" });
                        }
                      }}
                    />
                    {multiPayer && (
                      <View className="gap-2 mt-1">
                        {members.map((m) => {
                          const val = payerInputs[m.user.id] ?? "";
                          if (!val && val !== "") return null;
                          return (
                            <View key={m.user.id} className="flex-row items-center gap-2">
                              <Text className="flex-1 text-sm" numberOfLines={1}>
                                {m.user.display_name}
                              </Text>
                              <View className="w-28">
                                <Input
                                  value={val}
                                  onChangeText={(text) => {
                                    if (text === "" || /^\d*\.?\d{0,2}$/.test(text)) {
                                      setPayerInputs((prev) => ({ ...prev, [m.user.id]: text }));
                                    }
                                  }}
                                  keyboardType="decimal-pad"
                                  placeholder="0.00"
                                />
                              </View>
                              <Pressable
                                onPress={() => {
                                  setPayerInputs((prev) => {
                                    const next = { ...prev };
                                    delete next[m.user.id];
                                    return next;
                                  });
                                }}
                              >
                                <X size={16} color="hsl(0 84.2% 60.2%)" />
                              </Pressable>
                            </View>
                          );
                        })}
                        {/* 新增付款人按鈕 */}
                        {members.filter((m) => !(m.user.id in payerInputs)).length > 0 && (
                          <Pressable
                            onPress={() => {
                              const available = members.find((m) => !(m.user.id in payerInputs));
                              if (available) {
                                setPayerInputs((prev) => ({ ...prev, [available.user.id]: "" }));
                              }
                            }}
                            className="py-2"
                          >
                            <Text className="text-sm text-primary">{t("add_payer")}</Text>
                          </Pressable>
                        )}
                        {amount ? (() => {
                          const payerSum = Object.values(payerInputs).reduce((acc, v) => acc + (Number(v) || 0), 0);
                          const diff = Number(amount) - payerSum;
                          const isBalanced = Math.abs(diff) < 0.01;
                          return (
                            <Text className={`text-sm font-medium ${isBalanced ? "text-primary" : "text-destructive"}`}>
                              {diff >= 0 ? t("remaining") : t("exceeded")}: {Math.abs(diff).toFixed(2)}
                            </Text>
                          );
                        })() : null}
                      </View>
                    )}
                  </View>

                  {/* Participants */}
                  <View className="gap-2">
                    <View className="flex-row items-center justify-between">
                      <Text className="text-sm font-medium">
                        {t("participants")} ({selectedMembers.size}/{members.length})
                      </Text>
                      <Pressable onPress={toggleAllMembers}>
                        <Text className="text-sm text-primary">
                          {selectedMembers.size === members.length ? t("deselect_all") : t("select_all")}
                        </Text>
                      </Pressable>
                    </View>
                    <View className="flex-row flex-wrap gap-2">
                      {members.map((m) => {
                        const selected = selectedMembers.has(m.user.id);
                        return (
                          <Pressable
                            key={m.user.id}
                            onPress={() => {
                              toggleMember(m.user.id);
                              // 切換成員後，如果非 equal 方式，重新初始化該成員的 splitInput
                              if (splitMethod !== "equal") {
                                setSplitInputs((prev) => {
                                  const next = { ...prev };
                                  if (selected) {
                                    delete next[m.user.id];
                                  } else {
                                    next[m.user.id] = splitMethod === "shares" || splitMethod === "ratio" ? "1" : "";
                                  }
                                  return next;
                                });
                              }
                            }}
                            className={`flex-row items-center gap-1.5 px-3 py-2 rounded-full border ${
                              selected ? "bg-primary/10 border-primary" : "border-border"
                            }`}
                          >
                            {selected && <Check size={14} color="hsl(var(--primary))" />}
                            <Text className={`text-sm ${selected ? "text-primary font-medium" : "text-muted-foreground"}`}>
                              {m.user.display_name}
                            </Text>
                          </Pressable>
                        );
                      })}
                    </View>
                  </View>

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
                          setSelectedMembers(new Set(members.map((m) => m.user.id)));
                        }
                      }}
                    />
                  </View>

                  {splitMethod !== "equal" && selectedMembersList.length > 0 && (
                    <View className="gap-3">
                      <Text className="text-sm font-medium">{t("split_details")}</Text>
                      {selectedMembersList.map((m) => (
                        <View key={m.user.id} className="flex-row items-center gap-2">
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
                              placeholder={splitMethod === "exact" ? "0.00" : splitMethod === "ratio" ? "0" : "1"}
                              className={splitMethod === "ratio" ? "pr-7" : undefined}
                            />
                            {splitMethod === "ratio" && (
                              <View className="absolute right-2 top-0 bottom-0 justify-center pointer-events-none">
                                <Text className="text-sm text-muted-foreground">%</Text>
                              </View>
                            )}
                          </View>
                        </View>
                      ))}

                      {splitMethod === "exact" && amount ? (
                        (() => {
                          const total = Number(amount);
                          const sum = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
                          const diff = total - sum;
                          const isBalanced = Math.abs(diff) < 0.01;
                          return (
                            <Text className={`text-sm font-medium ${isBalanced ? "text-primary" : "text-destructive"}`}>
                              {diff >= 0 ? t("remaining") : t("exceeded")}: {Math.abs(diff).toFixed(2)}
                            </Text>
                          );
                        })()
                      ) : splitMethod === "ratio" && amount ? (
                        (() => {
                          const total = Number(amount);
                          const totalPct = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
                          const isBalanced = Math.abs(totalPct - 100) < 0.01;
                          return (
                            <View className="gap-1">
                              <Text className={`text-sm font-medium ${isBalanced ? "text-primary" : "text-destructive"}`}>
                                {t("total_percentage")}: {totalPct.toFixed(2)}%
                              </Text>
                              {totalPct > 0 && selectedMembersList.map((m) => {
                                const pct = Number(splitInputs[m.user.id]) || 0;
                                const est = (total * pct / 100).toFixed(2);
                                return (
                                  <Text key={m.user.id} className="text-xs text-muted-foreground">
                                    {m.user.display_name}: {expenseCurrency} {est}
                                  </Text>
                                );
                              })}
                            </View>
                          );
                        })()
                      ) : splitMethod === "shares" && amount ? (
                        (() => {
                          const total = Number(amount);
                          const totalShares = selectedMembersList.reduce((acc, m) => acc + (Number(splitInputs[m.user.id]) || 0), 0);
                          return (
                            <View className="gap-1">
                              <Text className="text-sm text-muted-foreground">
                                {t("total_shares_label")}: {totalShares}
                              </Text>
                              {totalShares > 0 && selectedMembersList.map((m) => {
                                const s = Number(splitInputs[m.user.id]) || 0;
                                const est = (total * s / totalShares).toFixed(2);
                                return (
                                  <Text key={m.user.id} className="text-xs text-muted-foreground">
                                    {m.user.display_name}: {expenseCurrency} {est}
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
                    onPress={handleSubmitExpense}
                    loading={adding}
                    disabled={adding || !canSubmitExpense}
                    size="lg"
                    className="mt-2"
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
        visible={showExpenseDiscardConfirm}
        onDiscard={handleDiscardExpense}
        onCancel={() => setShowExpenseDiscardConfirm(false)}
      />

      {/* Add Member Bottom Sheet */}
      <Modal
        visible={showAddMember}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAddMember(false)}
        onShow={fetchFriendsForAdd}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <Pressable className="flex-1" onPress={() => setShowAddMember(false)} />
          <View className="bg-background rounded-t-2xl px-5 pb-10 pt-4 max-h-[80%]">
            <View className="items-center mb-4">
              <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
            </View>

            <View className="flex-row items-center justify-between mb-4">
              <H3>{t("add_member_title")}</H3>
              <Pressable onPress={() => setShowAddMember(false)}>
                <X size={24} color="hsl(240 3.8% 46.1%)" />
              </Pressable>
            </View>

              <ScrollView className="flex-shrink" showsVerticalScrollIndicator={false}>
                <View className="gap-4">
                  {/* Friend selection section */}
                  <View>
                    <Text className="text-sm font-medium text-muted-foreground mb-2">{t("from_friends")}</Text>
                    {friendsLoading ? (
                      <ActivityIndicator size="small" className="py-4" />
                    ) : friendsForAdd.length === 0 ? (
                      <Muted className="py-2">{t("no_friends_to_add")}</Muted>
                    ) : (
                      <View className="gap-2">
                        {friendsForAdd.map((friend) => (
                          <Card key={friend.id}>
                            <CardContent className="flex-row items-center p-3 gap-3">
                              <View className="h-9 w-9 rounded-full bg-muted items-center justify-center">
                                <UsersThree size={18} color="hsl(240 3.8% 46.1%)" weight="regular" />
                              </View>
                              <View className="flex-1">
                                <Text className="font-medium text-sm">{friend.display_name}</Text>
                                <Muted className="text-xs">{friend.email}</Muted>
                              </View>
                              <Pressable
                                onPress={() => handleAddFriendAsMember(friend)}
                                disabled={addingFriendId === friend.id}
                                className="h-8 w-8 rounded-full bg-primary items-center justify-center"
                              >
                                {addingFriendId === friend.id ? (
                                  <ActivityIndicator size="small" color="white" />
                                ) : (
                                  <UserPlus size={16} color="white" weight="bold" />
                                )}
                              </Pressable>
                            </CardContent>
                          </Card>
                        ))}
                      </View>
                    )}
                  </View>

                  {/* Divider */}
                  <View className="flex-row items-center gap-3">
                    <View className="flex-1 h-px bg-border" />
                    <Muted className="text-xs">{t("or_search_by_email")}</Muted>
                    <View className="flex-1 h-px bg-border" />
                  </View>

                  {/* Email lookup section */}
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
                          <UsersThree size={20} color="hsl(240 3.8% 46.1%)" weight="regular" />
                        </View>
                        <View className="flex-1">
                          <Text className="font-medium">{foundUser.display_name}</Text>
                          <Muted>{foundUser.email}</Muted>
                        </View>
                      </CardContent>
                    </Card>
                  )}

                  {foundUser && (
                    <Button
                      onPress={handleAddMember}
                      loading={addingMember}
                      disabled={addingMember || !foundUser}
                      size="lg"
                    >
                      {t("add_member")}
                    </Button>
                  )}

                  {/* Divider */}
                  <View className="flex-row items-center gap-3 mt-2">
                    <View className="flex-1 h-px bg-border" />
                    <Muted className="text-xs">{t("or_invite_by_email")}</Muted>
                    <View className="flex-1 h-px bg-border" />
                  </View>

                  {/* Email invitation section */}
                  <View className="flex-row gap-2 items-end">
                    <View className="flex-1">
                      <Input
                        label={t("email")}
                        value={inviteEmail}
                        onChangeText={(text) => {
                          setInviteEmail(text);
                          setInviteError("");
                          setInviteSuccess("");
                        }}
                        placeholder={t("enter_email_to_invite")}
                        keyboardType="email-address"
                        autoCapitalize="none"
                      />
                    </View>
                    <Button
                      onPress={handleSendEmailInvitation}
                      loading={sendingInvite}
                      disabled={sendingInvite || !inviteEmail.trim()}
                      className="mb-0.5"
                    >
                      {t("send_invitation")}
                    </Button>
                  </View>

                  {inviteError ? (
                    <Text className="text-destructive text-sm">{inviteError}</Text>
                  ) : null}

                  {inviteSuccess ? (
                    <Text className="text-income text-sm">{inviteSuccess}</Text>
                  ) : null}
                </View>
              </ScrollView>
            </View>
        </KeyboardAvoidingView>
        </View>
      </Modal>

      {/* Group Settings Modal */}
      <Modal
        visible={showSettings}
        transparent
        animationType="slide"
        onRequestClose={() => setShowSettings(false)}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <Pressable className="flex-1" onPress={() => setShowSettings(false)} />
          <View className="bg-background rounded-t-2xl px-5 pb-10 pt-4">
            <View className="items-center mb-4">
              <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
            </View>
            <View className="flex-row items-center justify-between mb-6">
              <H3>{t("group_settings")}</H3>
              <Pressable onPress={() => setShowSettings(false)}>
                <X size={24} color="hsl(240 3.8% 46.1%)" />
              </Pressable>
            </View>
              <View className="gap-4">
                <Input
                  label={t("group_name")}
                  value={editGroupName}
                  onChangeText={(v) => { setEditGroupName(v); setSettingsError(null); }}
                  placeholder={t("group_name")}
                />
                <CurrencyPicker
                  label={t("default_currency")}
                  value={editGroupCurrency}
                  onSelect={setEditGroupCurrency}
                />
                <CoverImagePicker
                  label={t("cover_image_url")}
                  value={editCoverUrl}
                  onSelect={(url) => { setEditCoverUrl(url || ""); setSettingsError(null); }}
                />
                {settingsError ? (
                  <Text className="text-sm text-destructive">{settingsError}</Text>
                ) : null}
                <Button
                  onPress={async () => {
                    if (!id || !editGroupName.trim()) return;
                    setSettingsLoading(true);
                    setSettingsError(null);
                    try {
                      await groupsAPI.update(id, {
                        name: editGroupName.trim(),
                        default_currency: editGroupCurrency,
                        cover_image_url: editCoverUrl.trim() || null,
                      });
                      setGroupName(editGroupName.trim());
                      setGroupCurrency(editGroupCurrency);
                      setCoverImageUrl(editCoverUrl.trim() || null);
                      setShowSettings(false);
                      await fetchData();
                    } catch (e: any) {
                      const msg = e.response?.data?.detail || e.message || t("group_update_failed");
                      setSettingsError(msg);
                    } finally {
                      setSettingsLoading(false);
                    }
                  }}
                  loading={settingsLoading}
                  disabled={settingsLoading || !editGroupName.trim()}
                  size="lg"
                  className="mt-2"
                >
                  {t("save")}
                </Button>
              </View>
            </View>
        </KeyboardAvoidingView>
        </View>
      </Modal>

      {/* Settle Up Confirmation Modal */}
      <Modal
        visible={!!settleTarget}
        transparent
        animationType="fade"
        onRequestClose={() => setSettleTarget(null)}
      >
        <View className={`flex-1 ${themeClass}`}>
          <Pressable className="flex-1 justify-center items-center bg-black/50 px-6" onPress={() => setSettleTarget(null)}>
            <Pressable className="bg-background rounded-xl px-5 py-6 w-full max-w-sm">
              <H3 className="mb-4">{t("settle_up_confirm")}</H3>
              {settleTarget && (
                <>
                  <Text className="text-base mb-3">
                    {t("settle_up_confirm_msg", {
                      from: settleTarget.from_user_name,
                      amount: `${settleCurrency} ${parseFloat(settleAmount).toLocaleString()}`,
                      to: settleTarget.to_user_name,
                    })}
                  </Text>
                  <CurrencyPicker
                    value={settleCurrency}
                    onSelect={handleSettleCurrencyChange}
                    label={t("currency")}
                    className="mb-3"
                  />
                  {settleCurrency !== settleTarget.currency && settleRate != null && (
                    <Text className="text-sm text-muted-foreground mb-3">
                      {settleTarget.currency} {parseFloat(settleTarget.amount).toLocaleString()}
                      {" → "}
                      {settleCurrency} {parseFloat(settleAmount).toLocaleString()}
                      {`  (1 ${settleTarget.currency} = ${settleRate} ${settleCurrency})`}
                    </Text>
                  )}
                </>
              )}
              {settleError ? (
                <Text className="text-sm text-destructive mb-3">{settleError}</Text>
              ) : null}
              <View className="flex-row gap-3">
                <Button
                  variant="outline"
                  onPress={() => setSettleTarget(null)}
                  className="flex-1"
                  disabled={settling || converting}
                >
                  {t("cancel")}
                </Button>
                <Button
                  onPress={() => settleTarget && handleSettleUp(settleTarget)}
                  loading={settling}
                  disabled={settling || converting}
                  className="flex-1"
                >
                  {t("confirm")}
                </Button>
              </View>
            </Pressable>
          </Pressable>
        </View>
      </Modal>
      {/* Forgive debt confirmation Modal */}
      <Modal
        visible={!!forgiveTarget}
        transparent
        animationType="fade"
        onRequestClose={() => setForgiveTarget(null)}
      >
        <View className={`flex-1 ${themeClass}`}>
          <Pressable className="flex-1 justify-center items-center bg-black/50 px-6" onPress={() => setForgiveTarget(null)}>
            <Pressable className="bg-background rounded-xl px-5 py-6 w-full max-w-sm">
              <H3 className="mb-4">{t("forgive_debt_confirm")}</H3>
              {forgiveTarget && (
                <Text className="text-base mb-3">
                  {t("forgive_debt_confirm_msg", {
                    name: forgiveTarget.from_user_name,
                    amount: `${forgiveTarget.currency} ${parseFloat(forgiveTarget.amount).toLocaleString()}`,
                  })}
                </Text>
              )}
              {forgiveError ? (
                <Text className="text-sm text-destructive mb-3">{forgiveError}</Text>
              ) : null}
              <View className="flex-row gap-3">
                <Button
                  variant="outline"
                  onPress={() => setForgiveTarget(null)}
                  className="flex-1"
                  disabled={forgiving}
                >
                  {t("cancel")}
                </Button>
                <Button
                  onPress={() => forgiveTarget && handleForgive(forgiveTarget)}
                  loading={forgiving}
                  disabled={forgiving}
                  className="flex-1"
                >
                  {t("confirm")}
                </Button>
              </View>
            </Pressable>
          </Pressable>
        </View>
      </Modal>
      {/* Unified Currency Settlement Modal */}
      <Modal
        visible={!!unifiedSettleTarget}
        transparent
        animationType="fade"
        onRequestClose={() => { setUnifiedSettleTarget(null); setUnifiedSettleItems([]); }}
      >
        <View className={`flex-1 ${themeClass}`}>
          <Pressable className="flex-1 justify-center items-center bg-black/50 px-6" onPress={() => { setUnifiedSettleTarget(null); setUnifiedSettleItems([]); }}>
            <Pressable className="bg-background rounded-xl px-5 py-6 w-full max-w-sm">
              <H3 className="mb-4">{t("unified_settle_title")}</H3>
              {unifiedSettleTarget && (
                <>
                  <CurrencyPicker
                    value={unifiedSettleCurrency}
                    onSelect={handleUnifiedSettleCurrencyChange}
                    label={t("currency")}
                    className="mb-3"
                  />
                  {unifiedConverting ? (
                    <View className="items-center py-4">
                      <ActivityIndicator />
                      <Text className="text-sm text-muted-foreground mt-2">{t("unified_settle_converting")}</Text>
                    </View>
                  ) : (
                    <>
                      <Text className="text-sm text-muted-foreground mb-2">
                        {t("unified_settle_msg", { currency: unifiedSettleCurrency, name: unifiedSettleTarget.personName })}
                      </Text>
                      {unifiedSettleItems.map((item) => (
                        <View key={item.currency} className="flex-row items-center justify-between py-1.5 pl-2">
                          <Text className="text-sm text-muted-foreground flex-1">
                            {item.currency} {parseFloat(item.originalAmount).toLocaleString()}
                          </Text>
                          <Text className="text-sm font-medium">
                            {unifiedSettleCurrency} {item.convertedAmount.toLocaleString()}
                          </Text>
                        </View>
                      ))}
                      {unifiedSettleItems.length > 1 && (
                        <View className="flex-row items-center justify-between py-1.5 pl-2 border-t border-border mt-1 pt-2">
                          <Text className="text-sm font-semibold">{t("unified_settle_total")}</Text>
                          <Text className="text-base font-bold text-destructive">
                            {unifiedSettleCurrency} {unifiedSettleItems.reduce((sum, i) => sum + i.convertedAmount, 0).toLocaleString()}
                          </Text>
                        </View>
                      )}
                      <Text className="text-xs text-muted-foreground mt-2 mb-3">{t("unified_settle_round_hint")}</Text>
                    </>
                  )}
                </>
              )}
              {unifiedSettleError ? (
                <Text className="text-sm text-destructive mb-3">{unifiedSettleError}</Text>
              ) : null}
              <View className="flex-row gap-3">
                <Button
                  variant="outline"
                  onPress={() => { setUnifiedSettleTarget(null); setUnifiedSettleItems([]); }}
                  className="flex-1"
                  disabled={unifiedSettling || unifiedConverting}
                >
                  {t("cancel")}
                </Button>
                <Button
                  onPress={handleUnifiedSettleConfirm}
                  loading={unifiedSettling}
                  disabled={unifiedSettling || unifiedConverting || unifiedSettleItems.length === 0}
                  className="flex-1"
                >
                  {t("confirm")}
                </Button>
              </View>
            </Pressable>
          </Pressable>
        </View>
      </Modal>
    </View>
  );
}
