import { useState } from "react";
import { View, Pressable, ScrollView, Modal, KeyboardAvoidingView, Platform } from "react-native";
import { router } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  User,
  Mail,
  Globe,
  DollarSign,
  LogOut,
  Moon,
  Sun,
  Palette,
  ChevronRight,
  Check,
  X,
} from "lucide-react-native";
import { useAuthStore } from "../../stores/auth";
import { useTheme, COLOR_SCHEMES, type ColorScheme } from "~/lib/theme";
import i18n from "../../i18n";
import { Text, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Separator } from "~/components/ui/separator";
import { Avatar } from "~/components/ui/avatar";
import { Card, CardContent } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { authAPI } from "../../services/api";

const LANGUAGES = [
  { code: "zh-TW", label: "繁體中文" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語" },
];

const CURRENCIES = [
  { code: "TWD", name_zh: "新台幣", name_en: "New Taiwan Dollar", name_ja: "台湾ドル" },
  { code: "USD", name_zh: "美元", name_en: "US Dollar", name_ja: "米ドル" },
  { code: "EUR", name_zh: "歐元", name_en: "Euro", name_ja: "ユーロ" },
  { code: "JPY", name_zh: "日圓", name_en: "Japanese Yen", name_ja: "日本円" },
  { code: "GBP", name_zh: "英鎊", name_en: "British Pound", name_ja: "英ポンド" },
  { code: "AUD", name_zh: "澳幣", name_en: "Australian Dollar", name_ja: "豪ドル" },
  { code: "CAD", name_zh: "加拿大幣", name_en: "Canadian Dollar", name_ja: "カナダドル" },
  { code: "CNY", name_zh: "人民幣", name_en: "Chinese Yuan", name_ja: "人民元" },
  { code: "HKD", name_zh: "港幣", name_en: "Hong Kong Dollar", name_ja: "香港ドル" },
  { code: "KRW", name_zh: "韓元", name_en: "South Korean Won", name_ja: "韓国ウォン" },
  { code: "SGD", name_zh: "新加坡幣", name_en: "Singapore Dollar", name_ja: "シンガポールドル" },
  { code: "THB", name_zh: "泰銖", name_en: "Thai Baht", name_ja: "タイバーツ" },
];

interface SettingItemProps {
  icon: React.ReactNode;
  title: string;
  value?: string;
  onPress?: () => void;
  rightElement?: React.ReactNode;
}

function SettingItem({ icon, title, value, onPress, rightElement }: SettingItemProps) {
  return (
    <Pressable
      className="flex-row items-center py-3 px-1 active:opacity-70"
      onPress={onPress}
      disabled={!onPress}
    >
      <View className="h-9 w-9 items-center justify-center rounded-lg bg-muted mr-3">
        {icon}
      </View>
      <View className="flex-1">
        <Text className="text-base font-medium">{title}</Text>
        {value ? <Muted>{value}</Muted> : null}
      </View>
      {rightElement ?? (onPress ? (
        <ChevronRight size={20} color="hsl(240 3.8% 46.1%)" />
      ) : null)}
    </Pressable>
  );
}

function ColorSchemeOption({
  scheme,
  isSelected,
  onPress,
  isDark,
  label,
}: {
  scheme: (typeof COLOR_SCHEMES)[number];
  isSelected: boolean;
  onPress: () => void;
  isDark: boolean;
  label: string;
}) {
  const previewColor = isDark ? scheme.preview.dark : scheme.preview.light;

  return (
    <Pressable
      className={`flex-1 items-center p-2 rounded-xl border-2 ${
        isSelected ? "border-primary bg-primary/10" : "border-border bg-card"
      }`}
      onPress={onPress}
    >
      <View
        style={{ backgroundColor: previewColor, width: 28, height: 28, borderRadius: 14 }}
        className="mb-1 items-center justify-center"
      >
        {isSelected && <Check size={14} color="#fff" />}
      </View>
      <Text className={`text-xs font-medium ${isSelected ? "text-primary" : ""}`}>
        {label}
      </Text>
    </Pressable>
  );
}

export default function AccountScreen() {
  const { t } = useTranslation();
  const { user, logout, updateUser } = useAuthStore();
  const { isDark, toggleTheme, colorScheme, setColorScheme } = useTheme();

  // Display name modal
  const [showEditName, setShowEditName] = useState(false);
  const [editName, setEditName] = useState(user?.display_name || "");
  const [nameLoading, setNameLoading] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);

  // Language picker
  const [showLangPicker, setShowLangPicker] = useState(false);

  // Currency picker
  const [showCurrencyModal, setShowCurrencyModal] = useState(false);
  const [currencyLoading, setCurrencyLoading] = useState(false);

  const handleLogout = () => {
    logout();
    router.replace("/(auth)/login");
  };

  const currentLang =
    LANGUAGES.find((l) => l.code === i18n.language)?.label || "繁體中文";

  const getCurrencyDisplayName = (code: string): string => {
    const currency = CURRENCIES.find((c) => c.code === code);
    if (!currency) return code;

    if (i18n.language.startsWith("zh")) return currency.name_zh;
    if (i18n.language.startsWith("ja")) return currency.name_ja;
    return currency.name_en;
  };

  const handleEditName = async () => {
    if (!editName.trim()) {
      setNameError(t("display_name_required") || "Display name is required");
      return;
    }
    setNameLoading(true);
    setNameError(null);
    try {
      await authAPI.updateMe({ display_name: editName.trim() });
      updateUser({ display_name: editName.trim() });
      setShowEditName(false);
    } catch (e: any) {
      const msg = e?.response?.data?.detail || t("profile_update_failed");
      setNameError(msg);
    } finally {
      setNameLoading(false);
    }
  };

  const handleLanguageSelect = async (code: string) => {
    try {
      await i18n.changeLanguage(code);
      await authAPI.updateMe({ locale: code });
      updateUser({ locale: code });
      setShowLangPicker(false);
    } catch (e: any) {
      console.error("Language change failed:", e);
    }
  };

  const handleCurrencySelect = async (code: string) => {
    setCurrencyLoading(true);
    try {
      await authAPI.updateMe({ preferred_currency: code });
      updateUser({ preferred_currency: code });
      setShowCurrencyModal(false);
    } catch (e: any) {
      console.error("Currency change failed:", e);
    } finally {
      setCurrencyLoading(false);
    }
  };

  const iconColor = isDark ? "#A1A1AA" : "#71717A";

  return (
    <ScrollView className="flex-1 bg-background">
      {/* Profile Section */}
      <View className="items-center pt-8 pb-6">
        <Avatar name={user?.display_name || "?"} avatarUrl={user?.avatar_url} size="xl" index={0} />
        <Text className="mt-3 text-xl font-semibold">
          {user?.display_name}
        </Text>
        <Muted>{user?.email}</Muted>
      </View>

      {/* Color Scheme Picker */}
      <View className="px-5 mb-4">
        <Card>
          <CardContent className="p-4">
            <View className="flex-row items-center mb-3">
              <View className="h-9 w-9 items-center justify-center rounded-lg bg-muted mr-3">
                <Palette size={18} color={iconColor} />
              </View>
              <Text className="text-base font-medium">{t("color_scheme")}</Text>
            </View>
            <View className="gap-2">
              <View className="flex-row gap-2">
                {COLOR_SCHEMES.slice(0, 5).map((scheme) => (
                  <ColorSchemeOption
                    key={scheme.id}
                    scheme={scheme}
                    isSelected={colorScheme === scheme.id}
                    onPress={() => setColorScheme(scheme.id as ColorScheme)}
                    isDark={isDark}
                    label={t(scheme.labelKey)}
                  />
                ))}
              </View>
              <View className="flex-row gap-2">
                {COLOR_SCHEMES.slice(5, 10).map((scheme) => (
                  <ColorSchemeOption
                    key={scheme.id}
                    scheme={scheme}
                    isSelected={colorScheme === scheme.id}
                    onPress={() => setColorScheme(scheme.id as ColorScheme)}
                    isDark={isDark}
                    label={t(scheme.labelKey)}
                  />
                ))}
              </View>
            </View>
          </CardContent>
        </Card>
      </View>

      {/* Settings Card */}
      <View className="px-5">
        <Card>
          <CardContent className="p-4 gap-0">
            <SettingItem
              icon={<User size={18} color={iconColor} />}
              title={t("display_name")}
              value={user?.display_name}
              onPress={() => {
                setEditName(user?.display_name || "");
                setNameError(null);
                setShowEditName(true);
              }}
            />
            <Separator />
            <SettingItem
              icon={<Mail size={18} color={iconColor} />}
              title={t("email")}
              value={user?.email || "-"}
            />
            <Separator />
            <SettingItem
              icon={<Globe size={18} color={iconColor} />}
              title={t("language")}
              value={currentLang}
              onPress={() => setShowLangPicker(true)}
            />
            <Separator />
            <SettingItem
              icon={<DollarSign size={18} color={iconColor} />}
              title={t("preferred_currency")}
              value={getCurrencyDisplayName(user?.preferred_currency || "TWD")}
              onPress={() => setShowCurrencyModal(true)}
            />
            <Separator />
            <SettingItem
              icon={isDark
                ? <Moon size={18} color={iconColor} />
                : <Sun size={18} color={iconColor} />
              }
              title={isDark ? t("dark_mode") : t("light_mode")}
              onPress={toggleTheme}
            />
          </CardContent>
        </Card>

        <Button
          variant="destructive"
          onPress={handleLogout}
          className="mt-6 mb-8"
        >
          {t("logout")}
        </Button>
      </View>

      {/* Edit Display Name Modal */}
      <Modal
        visible={showEditName}
        transparent
        animationType="slide"
        onRequestClose={() => {
          setShowEditName(false);
          setNameError(null);
        }}
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
                <Text className="text-xl font-semibold">{t("edit_display_name")}</Text>
                <Pressable onPress={() => { setShowEditName(false); setNameError(null); }}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>
              <View className="gap-4">
                <Input
                  label={t("display_name")}
                  value={editName}
                  onChangeText={setEditName}
                  autoCapitalize="words"
                  editable={!nameLoading}
                />
                {nameError && (
                  <Text className="text-destructive text-sm">{nameError}</Text>
                )}
                <Button
                  onPress={handleEditName}
                  disabled={nameLoading || !editName.trim()}
                  className="mt-2"
                >
                  {nameLoading ? t("loading") : t("save")}
                </Button>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Language Picker Modal */}
      <Modal
        visible={showLangPicker}
        transparent
        animationType="slide"
        onRequestClose={() => setShowLangPicker(false)}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-background rounded-t-3xl px-5 pb-10 pt-4">
            <View className="items-center mb-4">
              <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
            </View>
            <View className="flex-row items-center justify-between mb-6">
              <Text className="text-xl font-semibold">{t("select_language")}</Text>
              <Pressable onPress={() => setShowLangPicker(false)}>
                <X size={24} color="hsl(240 3.8% 46.1%)" />
              </Pressable>
            </View>
            <View className="gap-3">
              {LANGUAGES.map((lang) => (
                <Pressable
                  key={lang.code}
                  className={`flex-row items-center p-3 rounded-lg border ${
                    i18n.language === lang.code
                      ? "border-primary bg-primary/10"
                      : "border-border bg-muted/50"
                  }`}
                  onPress={() => handleLanguageSelect(lang.code)}
                >
                  <Text
                    className={`flex-1 font-medium ${
                      i18n.language === lang.code ? "text-primary" : ""
                    }`}
                  >
                    {lang.label}
                  </Text>
                  {i18n.language === lang.code && (
                    <Check size={20} color="hsl(var(--color-primary))" />
                  )}
                </Pressable>
              ))}
            </View>
          </View>
        </View>
      </Modal>

      {/* Currency Picker Modal */}
      <Modal
        visible={showCurrencyModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCurrencyModal(false)}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-background rounded-t-3xl px-5 pb-10 pt-4">
            <View className="items-center mb-4">
              <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
            </View>
            <View className="flex-row items-center justify-between mb-6">
              <Text className="text-xl font-semibold">{t("select_currency")}</Text>
              <Pressable onPress={() => setShowCurrencyModal(false)}>
                <X size={24} color="hsl(240 3.8% 46.1%)" />
              </Pressable>
            </View>
            <ScrollView className="gap-2 max-h-96">
              {CURRENCIES.map((currency) => (
                <Pressable
                  key={currency.code}
                  className={`flex-row items-center p-3 rounded-lg border ${
                    user?.preferred_currency === currency.code
                      ? "border-primary bg-primary/10"
                      : "border-border bg-muted/50"
                  }`}
                  onPress={() => handleCurrencySelect(currency.code)}
                  disabled={currencyLoading}
                >
                  <View className="flex-1">
                    <Text className="font-medium">{currency.code}</Text>
                    <Muted className="text-xs">
                      {getCurrencyDisplayName(currency.code)}
                    </Muted>
                  </View>
                  {user?.preferred_currency === currency.code && (
                    <Check size={20} color="hsl(var(--color-primary))" />
                  )}
                </Pressable>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>

    </ScrollView>
  );
}
