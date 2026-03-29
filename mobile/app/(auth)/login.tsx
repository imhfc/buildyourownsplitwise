import { useState } from "react";
import { View, KeyboardAvoidingView, Platform } from "react-native";
import { router } from "expo-router";
import { useTranslation } from "react-i18next";
import * as WebBrowser from "expo-web-browser";
import * as AuthSession from "expo-auth-session";
import { authAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { H1, Muted, Text } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";

WebBrowser.maybeCompleteAuthSession();

const GOOGLE_CLIENT_ID = Platform.select({
  ios: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
  android: process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID,
  default: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
}) ?? "";

const discovery = {
  authorizationEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
  tokenEndpoint: "https://oauth2.googleapis.com/token",
};

const redirectUri = AuthSession.makeRedirectUri({
  scheme: "byosw",
  preferLocalhost: false,
});

export default function LoginScreen() {
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [, , promptAsync] = AuthSession.useAuthRequest(
    {
      clientId: GOOGLE_CLIENT_ID,
      scopes: ["openid", "profile", "email"],
      redirectUri,
      responseType: AuthSession.ResponseType.Token,
    },
    discovery,
  );

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

  const handleGoogleLogin = async () => {
    setError("");
    setLoading(true);
    try {
      const result = await promptAsync();
      if (result.type !== "success") {
        return;
      }
      const accessToken = result.params?.access_token;
      if (!accessToken) {
        setError(t("google_sign_in_failed"));
        return;
      }
      const res = await authAPI.googleLogin(accessToken);
      setAuth(res.data.access_token, res.data.refresh_token, res.data.user);
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.response?.data?.detail || t("google_sign_in_failed"));
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
