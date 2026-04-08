import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { View, ScrollView, RefreshControl, ActivityIndicator, Pressable } from "react-native";
import { useTranslation } from "react-i18next";
import { CaretDown, CaretRight } from "phosphor-react-native";
import { Card, CardContent } from "~/components/ui/card";
import { Text, Muted } from "~/components/ui/text";
import { EmptyState } from "~/components/ui/empty-state";
import { ArrowsLeftRight } from "phosphor-react-native";
import { exchangeRatesAPI, settlementsAPI } from "~/services/api";
import type { Suggestion, CurrencyGroupSuggestions } from "./types";

interface BalancesTabProps {
  suggestionsByCurrency: CurrencyGroupSuggestions[];
  suggestions: Suggestion[];
  userId: string;
  preferredCurrency: string;
  groupId: string;
  groupCurrency: string;
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  listHeader: React.ReactNode;
}

interface CurrencyBalance {
  currency: string;
  items: { label: string; amount: number; isOwedToMe: boolean }[];
  subtotal: number;
}

interface ConvertedTotal {
  currency: string;
  original: number;
  converted: number;
  rate: number | null;
}

export function BalancesTab({
  suggestionsByCurrency,
  suggestions,
  userId,
  preferredCurrency,
  groupId,
  loading,
  refreshing,
  onRefresh,
  listHeader,
}: BalancesTabProps) {
  const { t } = useTranslation();
  const [convertedTotals, setConvertedTotals] = useState<ConvertedTotal[]>([]);
  const [converting, setConverting] = useState(false);

  // Pairwise debt details (expandable)
  const [pairwiseDetails, setPairwiseDetails] = useState<Suggestion[]>([]);
  const [showDetails, setShowDetails] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);

  // Compute per-currency balances for current user
  const currencyBalances: CurrencyBalance[] = suggestionsByCurrency.map((group) => {
    const items: CurrencyBalance["items"] = [];
    for (const s of group.suggestions) {
      if (s.to_user_id === userId) {
        items.push({
          label: t("owes_you", { name: s.from_user_name }),
          amount: parseFloat(s.amount),
          isOwedToMe: true,
        });
      } else if (s.from_user_id === userId) {
        items.push({
          label: t("you_owe_person", { name: s.to_user_name }),
          amount: parseFloat(s.amount),
          isOwedToMe: false,
        });
      }
    }
    const subtotal = items.reduce(
      (sum, item) => sum + (item.isOwedToMe ? item.amount : -item.amount),
      0,
    );
    return { currency: group.currency, items, subtotal };
  }).filter((cb) => cb.items.length > 0);

  // Stable key for useEffect dependency (avoid re-triggering on every render)
  const balancesKey = useMemo(
    () => JSON.stringify(currencyBalances.map((cb) => ({ c: cb.currency, s: cb.subtotal }))),
    [suggestionsByCurrency, userId],
  );

  // Convert subtotals to preferred currency for grand total
  // Use a ref to track the latest request and avoid stale cancellation
  const convertRequestId = useRef(0);
  useEffect(() => {
    if (currencyBalances.length === 0) {
      setConvertedTotals([]);
      setConverting(false);
      return;
    }

    const requestId = ++convertRequestId.current;
    const doConvert = async () => {
      setConverting(true);
      try {
        const results: ConvertedTotal[] = await Promise.all(
          currencyBalances.map(async (cb) => {
            if (cb.currency === preferredCurrency) {
              return { currency: cb.currency, original: cb.subtotal, converted: cb.subtotal, rate: null };
            }
            try {
              const res = await exchangeRatesAPI.convert({
                from_currency: cb.currency,
                to_currency: preferredCurrency,
                amount: Math.abs(cb.subtotal),
              });
              const convertedAmount = cb.subtotal >= 0 ? res.data.converted_amount : -res.data.converted_amount;
              return { currency: cb.currency, original: cb.subtotal, converted: convertedAmount, rate: res.data.rate };
            } catch {
              return { currency: cb.currency, original: cb.subtotal, converted: cb.subtotal, rate: null };
            }
          }),
        );
        if (requestId === convertRequestId.current) setConvertedTotals(results);
      } finally {
        if (requestId === convertRequestId.current) setConverting(false);
      }
    };
    doConvert();
  }, [balancesKey, preferredCurrency]);

  const grandTotal = convertedTotals.reduce((sum, ct) => sum + ct.converted, 0);
  const hasMultipleCurrencies = currencyBalances.length > 1;
  const hasSuggestions = suggestions.length > 0;

  if (loading) {
    return (
      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 100 }}>
        {listHeader}
        <View className="items-center justify-center py-20">
          <ActivityIndicator size="large" />
        </View>
      </ScrollView>
    );
  }

  if (currencyBalances.length === 0) {
    return (
      <ScrollView
        contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {listHeader}
        <EmptyState
          icon={ArrowsLeftRight}
          title={t("balanced")}
          description={t("all_balanced_hint")}
        />
      </ScrollView>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 100 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {listHeader}

      {/* Per-currency balance cards with individual items */}
      {currencyBalances.map((cb) => (
        <Card key={cb.currency} className="mb-2">
          <CardContent className="p-3.5">
            {hasMultipleCurrencies && (
              <Text className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                {cb.currency}
              </Text>
            )}
            {cb.items.map((item, i) => (
              <View key={i} className="flex-row items-center justify-between py-1">
                <Text className="text-sm font-medium text-foreground flex-1">{item.label}</Text>
                <Text
                  className={`text-sm font-semibold tabular-nums ${
                    item.isOwedToMe ? "text-income" : "text-destructive"
                  }`}
                >
                  {item.isOwedToMe ? "+" : "-"}{cb.currency} {item.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Text>
              </View>
            ))}
            {cb.items.length > 1 && (
              <View className="flex-row items-center justify-between pt-2 mt-1 border-t border-border">
                <Text className="text-xs text-muted-foreground">{t("currency_subtotal")}</Text>
                <Text
                  className={`text-sm font-semibold tabular-nums ${
                    cb.subtotal >= 0 ? "text-income" : "text-destructive"
                  }`}
                >
                  {cb.subtotal >= 0 ? "+" : "-"}{cb.currency} {Math.abs(cb.subtotal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Text>
              </View>
            )}
          </CardContent>
        </Card>
      ))}

      {/* Grand Total Card — preferred currency conversion */}
      {(hasMultipleCurrencies || currencyBalances[0]?.currency !== preferredCurrency) && (
        <Card className="mb-2 border-primary/30">
          <CardContent className="p-3.5 items-center gap-1">
            <Text className="text-xs text-muted-foreground">
              {t("grand_total_note", { currency: preferredCurrency })}
            </Text>
            {converting ? (
              <ActivityIndicator size="small" />
            ) : (
              <Text
                className={`text-lg font-semibold tabular-nums ${
                  grandTotal >= 0 ? "text-income" : "text-destructive"
                }`}
              >
                {grandTotal >= 0 ? "+" : "-"}
                {preferredCurrency} {Math.abs(grandTotal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Text>
            )}
          </CardContent>
        </Card>
      )}

      {/* Pairwise debt details (expandable) */}
      {hasSuggestions && (
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
                  const res = await settlementsAPI.pairwiseDetails(groupId);
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
    </ScrollView>
  );
}
