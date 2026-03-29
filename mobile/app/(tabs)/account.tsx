import { useState } from "react";
import { View, Pressable, ScrollView, Modal, KeyboardAvoidingView, Platform, Alert } from "react-native";
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
  Lock,
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
  const { user, logout } = useAuthStore();
  const { isDark, toggleTheme, colorScheme, setColorScheme } = useTheme();

  const [showChangePw, setShowChangePw] = useState(false);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwLoading, setPwLoading] = useState(false);

  const isEmailUser = user?.auth_provider === "email";

  const handleLogout = () => {
    logout();
    router.replace("/(auth)/login");
  };

  const cycleLanguage = () => {
    const currentIdx = LANGUAGES.findIndex((l) => l.code === i18n.language);
    const next = LANGUAGES[(currentIdx + 1) % LANGUAGES.length];
    i18n.changeLanguage(next.code);
  };

  const currentLang =
    LANGUAGES.find((l) => l.code === i18n.language)?.label || "繁體中文";

  const resetPwForm = () => {
    setOldPw("");
    setNewPw("");
    setConfirmPw("");
  };

  const handleChangePw = async () => {
    if (!oldPw || !newPw || !confirmPw) return;
    if (newPw !== confirmPw) {
      Alert.alert(t("error"), t("password_mismatch"));
      return;
    }
    setPwLoading(true);
    try {
      await authAPI.changePassword(oldPw, newPw);
      setShowChangePw(false);
      resetPwForm();
      Alert.alert("", t("password_changed"));
    } catch (e: any) {
      const msg = e?.response?.data?.detail || t("error");
      Alert.alert(t("error"), msg);
    } finally {
      setPwLoading(false);
    }
  };

  const iconColor = isDark ? "#A1A1AA" : "#71717A";

  return (
    <ScrollView className="flex-1 bg-background">
      {/* Profile Section */}
      <View className="items-center pt-8 pb-6">
        <Avatar name={user?.display_name || "?"} size="xl" index={0} />
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
              onPress={cycleLanguage}
            />
            <Separator />
            <SettingItem
              icon={<DollarSign size={18} color={iconColor} />}
              title={t("preferred_currency")}
              value={user?.preferred_currency || "TWD"}
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
            {isEmailUser && (
              <>
                <Separator />
                <SettingItem
                  icon={<Lock size={18} color={iconColor} />}
                  title={t("change_password")}
                  onPress={() => setShowChangePw(true)}
                />
              </>
            )}
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

      {/* Change Password Modal */}
      <Modal
        visible={showChangePw}
        transparent
        animationType="slide"
        onRequestClose={() => {
          setShowChangePw(false);
          resetPwForm();
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
                <Text className="text-xl font-semibold">{t("change_password")}</Text>
                <Pressable onPress={() => { setShowChangePw(false); resetPwForm(); }}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>
              <View className="gap-4">
                <Input
                  label={t("old_password")}
                  value={oldPw}
                  onChangeText={setOldPw}
                  secureTextEntry
                  autoCapitalize="none"
                />
                <Input
                  label={t("new_password")}
                  value={newPw}
                  onChangeText={setNewPw}
                  secureTextEntry
                  autoCapitalize="none"
                />
                <Input
                  label={t("confirm_new_password")}
                  value={confirmPw}
                  onChangeText={setConfirmPw}
                  secureTextEntry
                  autoCapitalize="none"
                />
                <Button
                  onPress={handleChangePw}
                  disabled={pwLoading || !oldPw || !newPw || !confirmPw}
                  className="mt-2"
                >
                  {pwLoading ? t("loading") : t("save")}
                </Button>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </ScrollView>
  );
}
