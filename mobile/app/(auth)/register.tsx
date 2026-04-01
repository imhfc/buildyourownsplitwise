import { useState } from "react";
import { View, KeyboardAvoidingView, Platform } from "react-native";
import { router } from "expo-router";
import { useTranslation } from "react-i18next";
import { authAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { H1, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";

export default function RegisterScreen() {
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async () => {
    if (!displayName || !email || !password) return;
    setLoading(true);
    setError("");
    try {
      const res = await authAPI.register({
        email,
        password,
        display_name: displayName,
      });
      setAuth(res.data.access_token, res.data.refresh_token, res.data.user);
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-background"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View className="flex-1 justify-center px-6">
        <H1 className="text-center text-primary mb-1">{t("app_name")}</H1>
        <Muted className="text-center mb-8">{t("register")}</Muted>

        <View className="gap-3">
          <Input
            label={t("display_name")}
            value={displayName}
            onChangeText={setDisplayName}
            placeholder={t("display_name")}
          />
          <Input
            label={t("email")}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            placeholder="you@example.com"
          />
          <Input
            label={t("password")}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholder="********"
            error={error || undefined}
          />
        </View>

        <Button
          onPress={handleRegister}
          loading={loading}
          className="mt-6"
        >
          {t("register")}
        </Button>

        <Button
          variant="ghost"
          onPress={() => router.canGoBack() ? router.back() : router.replace("/(auth)/login")}
          className="mt-3"
        >
          {t("login")}
        </Button>
      </View>
    </KeyboardAvoidingView>
  );
}
