import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  FlatList,
  Modal,
  Pressable,
  TextInput,
  View,
} from "react-native";
import { Check, CaretDown, MagnifyingGlass, X } from "phosphor-react-native";
import { useTranslation } from "react-i18next";
import { exchangeRatesAPI } from "../../services/api";
import { cn } from "~/lib/utils";
import { Text, H3, Muted } from "./text";

interface CurrencyInfo {
  code: string;
  name_zh: string;
  name_en: string;
}

interface CurrencyPickerProps {
  value: string;
  onSelect: (code: string) => void;
  label?: string;
  className?: string;
}

export function CurrencyPicker({
  value,
  onSelect,
  label,
  className,
}: CurrencyPickerProps) {
  const { t, i18n } = useTranslation();
  const [visible, setVisible] = useState(false);
  const [currencies, setCurrencies] = useState<CurrencyInfo[]>([]);
  const [search, setSearch] = useState("");
  const searchRef = useRef<TextInput>(null);
  const isZh = i18n.language.startsWith("zh");

  const fetchCurrencies = useCallback(async () => {
    try {
      const res = await exchangeRatesAPI.currencies();
      setCurrencies(res.data);
    } catch {
      // 如果 API 失敗，使用預設清單
      setCurrencies([
        { code: "TWD", name_zh: "新台幣", name_en: "New Taiwan Dollar" },
        { code: "USD", name_zh: "美元", name_en: "US Dollar" },
        { code: "EUR", name_zh: "歐元", name_en: "Euro" },
        { code: "JPY", name_zh: "日圓", name_en: "Japanese Yen" },
        { code: "GBP", name_zh: "英鎊", name_en: "British Pound" },
        { code: "AUD", name_zh: "澳幣", name_en: "Australian Dollar" },
        { code: "CAD", name_zh: "加拿大幣", name_en: "Canadian Dollar" },
        { code: "CNY", name_zh: "人民幣", name_en: "Chinese Yuan" },
        { code: "HKD", name_zh: "港幣", name_en: "Hong Kong Dollar" },
        { code: "KRW", name_zh: "韓元", name_en: "South Korean Won" },
        { code: "SGD", name_zh: "新加坡幣", name_en: "Singapore Dollar" },
        { code: "THB", name_zh: "泰銖", name_en: "Thai Baht" },
      ]);
    }
  }, []);

  useEffect(() => {
    if (visible && currencies.length === 0) {
      fetchCurrencies();
    }
  }, [visible, currencies.length, fetchCurrencies]);

  const filtered = useMemo(() => {
    if (!search.trim()) return currencies;
    const q = search.trim().toLowerCase();
    return currencies.filter(
      (c) =>
        c.code.toLowerCase().includes(q) ||
        c.name_zh.includes(q) ||
        c.name_en.toLowerCase().includes(q)
    );
  }, [currencies, search]);

  const selectedLabel = useMemo(() => {
    const found = currencies.find((c) => c.code === value);
    if (found) return `${found.code} - ${isZh ? found.name_zh : found.name_en}`;
    return value;
  }, [currencies, value, isZh]);

  const handleSelect = (code: string) => {
    onSelect(code);
    setVisible(false);
    setSearch("");
  };

  const renderItem = ({ item }: { item: CurrencyInfo }) => {
    const isSelected = item.code === value;
    return (
      <Pressable
        className={cn(
          "flex-row items-center px-4 py-3.5 border-b border-border",
          isSelected && "bg-primary/10"
        )}
        onPress={() => handleSelect(item.code)}
      >
        <Text className="text-base font-semibold w-14">{item.code}</Text>
        <Text className="flex-1 text-base text-muted-foreground">
          {isZh ? item.name_zh : item.name_en}
        </Text>
        {isSelected && <Check size={20} color="hsl(142.1 76.2% 36.3%)" />}
      </Pressable>
    );
  };

  return (
    <View className={cn("gap-1.5", className)}>
      {label ? (
        <Text className="text-sm font-medium text-foreground">{label}</Text>
      ) : null}

      <Pressable
        className="h-12 rounded-lg border border-input bg-background px-4 flex-row items-center justify-between"
        onPress={() => setVisible(true)}
      >
        <Text className="text-base text-foreground">{selectedLabel}</Text>
        <CaretDown size={18} color="hsl(240 3.8% 46.1%)" weight="regular" />
      </Pressable>

      <Modal
        visible={visible}
        transparent
        animationType="slide"
        onRequestClose={() => {
          setVisible(false);
          setSearch("");
        }}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-background rounded-t-2xl max-h-[75%]">
            {/* Header */}
            <View className="px-5 pt-4 pb-2">
              <View className="items-center mb-3">
                <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
              </View>
              <View className="flex-row items-center justify-between mb-3">
                <H3>{t("select_currency")}</H3>
                <Pressable
                  onPress={() => {
                    setVisible(false);
                    setSearch("");
                  }}
                >
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              {/* Search */}
              <View className="flex-row items-center h-11 rounded-lg border border-input bg-background px-3 mb-2">
                <MagnifyingGlass size={18} color="hsl(240 3.8% 46.1%)" weight="regular" />
                <TextInput
                  ref={searchRef}
                  className="flex-1 ml-2 text-base text-foreground"
                  placeholder={t("search_currency")}
                  placeholderTextColor="hsl(240 3.8% 46.1%)"
                  defaultValue={search}
                  onChangeText={setSearch}
                  autoFocus
                />
                {search ? (
                  <Pressable onPress={() => {
                    setSearch("");
                    searchRef.current?.setNativeProps({ text: "" });
                  }}>
                    <X size={16} color="hsl(240 3.8% 46.1%)" />
                  </Pressable>
                ) : null}
              </View>
            </View>

            {/* List */}
            <FlatList
              data={filtered}
              keyExtractor={(item) => item.code}
              renderItem={renderItem}
              keyboardShouldPersistTaps="handled"
              ListEmptyComponent={
                <View className="items-center py-10">
                  <Muted>{t("no_results")}</Muted>
                </View>
              }
            />
          </View>
        </View>
      </Modal>
    </View>
  );
}
