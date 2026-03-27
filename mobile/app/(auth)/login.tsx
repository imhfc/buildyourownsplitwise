import { useState } from "react";
import { View, StyleSheet, KeyboardAvoidingView, Platform } from "react-native";
import { Button, Text, TextInput, HelperText } from "react-native-paper";
import { router } from "expo-router";
import { useTranslation } from "react-i18next";
import { authAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";

export default function LoginScreen() {
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!email || !password) return;
    setLoading(true);
    setError("");
    try {
      const res = await authAPI.login({ email, password });
      setAuth(res.data.access_token, res.data.user);
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.inner}>
        <Text variant="headlineLarge" style={styles.title}>
          {t("app_name")}
        </Text>
        <Text variant="bodyLarge" style={styles.subtitle}>
          {t("login")}
        </Text>

        <TextInput
          label={t("email")}
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          style={styles.input}
          mode="outlined"
        />
        <TextInput
          label={t("password")}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.input}
          mode="outlined"
        />

        {error ? <HelperText type="error">{error}</HelperText> : null}

        <Button
          mode="contained"
          onPress={handleLogin}
          loading={loading}
          disabled={loading}
          style={styles.button}
        >
          {t("login")}
        </Button>

        <Button
          mode="text"
          onPress={() => router.push("/(auth)/register")}
          style={styles.link}
        >
          {t("register")}
        </Button>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  inner: { flex: 1, justifyContent: "center", padding: 24 },
  title: { textAlign: "center", fontWeight: "bold", color: "#2563EB", marginBottom: 4 },
  subtitle: { textAlign: "center", color: "#666", marginBottom: 32 },
  input: { marginBottom: 12 },
  button: { marginTop: 8, paddingVertical: 4 },
  link: { marginTop: 12 },
});
