import { View, Pressable } from "react-native";
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
  ChevronRight,
} from "lucide-react-native";
import { useAuthStore } from "../../stores/auth";
import { useTheme } from "~/lib/theme";
import i18n from "../../i18n";
import { Text, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Separator } from "~/components/ui/separator";
import { Avatar } from "~/components/ui/avatar";
import { Card, CardContent } from "~/components/ui/card";

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

export default function SettingsScreen() {
  const { t } = useTranslation();
  const { user, logout } = useAuthStore();
  const { isDark, toggleTheme } = useTheme();

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

  const iconColor = isDark ? "#A1A1AA" : "#71717A";

  return (
    <View className="flex-1 bg-background">
      {/* Profile Section */}
      <View className="items-center pt-8 pb-6">
        <Avatar name={user?.display_name || "?"} size="xl" index={0} />
        <Text className="mt-3 text-xl font-semibold">
          {user?.display_name}
        </Text>
        <Muted>{user?.email}</Muted>
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
              title={isDark ? "深色模式" : "淺色模式"}
              onPress={toggleTheme}
            />
          </CardContent>
        </Card>

        <Button
          variant="destructive"
          onPress={handleLogout}
          className="mt-6"
        >
          {t("logout")}
        </Button>
      </View>
    </View>
  );
}
