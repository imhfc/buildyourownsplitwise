import { View, StyleSheet } from "react-native";
import { List, Button, Divider, Text } from "react-native-paper";
import { router } from "expo-router";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../stores/auth";
import i18n from "../../i18n";

const LANGUAGES = [
  { code: "zh-TW", label: "繁體中文" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語" },
];

export default function SettingsScreen() {
  const { t } = useTranslation();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.replace("/(auth)/login");
  };

  const cycleLanguage = () => {
    const currentIdx = LANGUAGES.findIndex((l) => l.code === i18n.language);
    const next = LANGUAGES[(currentIdx + 1) % LANGUAGES.length];
    i18n.changeLanguage(next.code);
  };

  const currentLang = LANGUAGES.find((l) => l.code === i18n.language)?.label || "繁體中文";

  return (
    <View style={styles.container}>
      <List.Section>
        <List.Subheader>{t("settings")}</List.Subheader>
        <List.Item
          title={t("display_name")}
          description={user?.display_name}
          left={(props) => <List.Icon {...props} icon="account" />}
        />
        <List.Item
          title={t("email")}
          description={user?.email || "-"}
          left={(props) => <List.Icon {...props} icon="email" />}
        />
        <Divider />
        <List.Item
          title={t("language")}
          description={currentLang}
          left={(props) => <List.Icon {...props} icon="translate" />}
          onPress={cycleLanguage}
        />
        <List.Item
          title={t("preferred_currency")}
          description={user?.preferred_currency || "TWD"}
          left={(props) => <List.Icon {...props} icon="currency-usd" />}
        />
      </List.Section>

      <View style={styles.logoutContainer}>
        <Button mode="outlined" onPress={handleLogout} textColor="#EF4444">
          {t("logout")}
        </Button>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  logoutContainer: { padding: 24 },
});
