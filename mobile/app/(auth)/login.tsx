import { useState, useEffect } from "react";
import { View, KeyboardAvoidingView, Platform } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useTranslation } from "react-i18next";
import { authAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { H1, Muted, Text } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";

const GOOGLE_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID ?? "";

function buildGoogleOAuthUrl() {
  const redirectUri = Platform.OS === "web"
    ? window.location.origin
    : "https://byosw.duckdns.org";

  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: redirectUri,
    response_type: "token",
    scope: "openid profile email",
    prompt: "select_account",
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
}

function getHashParams(): Record<string, string> {
  if (Platform.OS !== "web") return {};
  const hash = window.location.hash.substring(1);
  if (!hash) return {};
  const params: Record<string, string> = {};
  hash.split("&").forEach((pair) => {
    const [key, value] = pair.split("=");
    params[decodeURIComponent(key)] = decodeURIComponent(value || "");
  });
  return params;
}

export default function LoginScreen() {
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Handle Google OAuth callback (implicit flow returns token in URL hash)
  useEffect(() => {
    if (Platform.OS !== "web") return;
    const params = getHashParams();
    const accessToken = params.access_token;
    if (!accessToken) return;

    // Clear the hash from URL
    window.history.replaceState(null, "", window.location.pathname);

    setLoading(true);
    authAPI
      .googleLogin(accessToken)
      .then((res) => {
        setAuth(res.data.access_token, res.data.refresh_token, res.data.user);
        router.replace("/(tabs)");
      })
      .catch((e: any) => {
        setError(e.response?.data?.detail || t("google_sign_in_failed"));
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogin = async () => {
    if (!email || !password) return;
    setLoading(true);
    setError("");
    try {
      const res = await authAPI.login({ email, password });
      setAuth(res.data.access_token, res.data.refresh_token, res.data.user);
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    if (!GOOGLE_CLIENT_ID) {
      setError("Google Client ID not configured");
      return;
    }
    window.location.href = buildGoogleOAuthUrl();
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-background"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View className="flex-1 justify-center px-6">
        <H1 className="text-center text-primary mb-1">{t("app_name")}</H1>
        <Muted className="text-center mb-8">{t("login")}</Muted>

        <View className="gap-3">
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
          onPress={handleLogin}
          loading={loading}
          className="mt-6"
        >
          {t("login")}
        </Button>

        <View className="flex-row items-center my-4 gap-3">
          <View className="flex-1 h-px bg-border" />
          <Text className="text-muted-foreground text-sm">{t("or")}</Text>
          <View className="flex-1 h-px bg-border" />
        </View>

        <Button
          variant="outline"
          onPress={handleGoogleLogin}
          loading={loading}
        >
          {t("sign_in_with_google")}
        </Button>

        <Button
          variant="ghost"
          onPress={() => router.push("/(auth)/register")}
          className="mt-3"
        >
          {t("register")}
        </Button>
      </View>
    </KeyboardAvoidingView>
  );
}
