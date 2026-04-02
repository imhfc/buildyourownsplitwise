import { useState, useEffect, useRef } from "react";
import {
  View,
  Platform,
  Animated,
  Easing,
} from "react-native";
import { router } from "expo-router";
import { useTranslation } from "react-i18next";
import { authAPI } from "../../services/api";
import { useAuthStore } from "../../stores/auth";
import { Logo } from "~/components/Logo";
import { Text } from "~/components/ui/text";
import { Button } from "~/components/ui/button";

const USE_NATIVE = Platform.OS !== "web";

/* ────────────────────────────────────────────
   Stagger fade-in wrapper
   ──────────────────────────────────────────── */

function FadeUp({
  delay,
  children,
}: {
  delay: number;
  children: React.ReactNode;
}) {
  const opacity = useRef(new Animated.Value(0)).current;
  const ty = useRef(new Animated.Value(28)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 700,
        delay,
        useNativeDriver: USE_NATIVE,
      }),
      Animated.timing(ty, {
        toValue: 0,
        duration: 700,
        delay,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: USE_NATIVE,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View style={{ opacity, transform: [{ translateY: ty }] }}>
      {children}
    </Animated.View>
  );
}

/* ────────────────────────────────────────────
   Google OAuth helpers
   ──────────────────────────────────────────── */

const GOOGLE_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID ?? "";

function buildGoogleOAuthUrl() {
  const redirectUri =
    Platform.OS === "web"
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

/* ────────────────────────────────────────────
   Login Screen
   ──────────────────────────────────────────── */

export default function LoginScreen() {
  const { t } = useTranslation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Brand entrance: scale + fade
  const brandScale = useRef(new Animated.Value(0.8)).current;
  const brandOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(brandScale, {
        toValue: 1,
        friction: 6,
        tension: 40,
        useNativeDriver: USE_NATIVE,
      }),
      Animated.timing(brandOpacity, {
        toValue: 1,
        duration: 900,
        useNativeDriver: USE_NATIVE,
      }),
    ]).start();
  }, []);

  // Google OAuth callback
  useEffect(() => {
    if (Platform.OS !== "web") return;
    const params = getHashParams();
    const accessToken = params.access_token;
    if (!accessToken) return;

    window.history.replaceState(null, "", window.location.pathname);

    setLoading(true);
    authAPI
      .googleLogin(accessToken)
      .then((res) => {
        setAuth(res.data.access_token, res.data.refresh_token, res.data.user);
        const pending = useAuthStore.getState().pendingInviteToken;
        if (pending) {
          useAuthStore.getState().setPendingInviteToken(null);
          if (pending.startsWith("email:")) {
            router.replace(`/invite/email/${pending.slice(6)}`);
          } else {
            router.replace(`/join/${pending}`);
          }
        } else {
          router.replace("/(tabs)");
        }
      })
      .catch((e: any) => {
        setError(e.response?.data?.detail || t("google_sign_in_failed"));
      })
      .finally(() => setLoading(false));
  }, []);

  const handleGoogleLogin = () => {
    if (!GOOGLE_CLIENT_ID) {
      setError(t("google_sign_in_failed"));
      return;
    }
    window.location.href = buildGoogleOAuthUrl();
  };

  return (
    <View className="flex-1 bg-background">
      <View
        className="flex-1 justify-center px-8"
        style={{ maxWidth: 420, alignSelf: "center", width: "100%" }}
      >
        {/* ── Brand area ── */}
        <Animated.View
          style={{
            opacity: brandOpacity,
            transform: [{ scale: brandScale }],
          }}
        >
          <View className="items-center mb-16">
            {/* App logo */}
            <View className="mb-7">
              <Logo size={96} />
            </View>

            {/* App name */}
            <Text className="text-3xl font-bold text-primary tracking-[0.35em]">
              {t("app_name")}
            </Text>

            {/* Decorative line */}
            <View className="bg-border mt-4 mb-3" style={{ width: 48, height: 2 }} />

            {/* Subtitle */}
            <Text className="text-base text-muted-foreground text-center px-4 leading-6">
              {t("app_subtitle")}
            </Text>
          </View>
        </Animated.View>

        {/* ── Error banner ── */}
        {error ? (
          <FadeUp delay={0}>
            <View className="border border-destructive rounded-lg px-4 py-3 mb-4">
              <Text className="text-destructive text-sm text-center">
                {error}
              </Text>
            </View>
          </FadeUp>
        ) : null}

        {/* ── Google sign-in CTA ── */}
        <FadeUp delay={600}>
          <Button onPress={handleGoogleLogin} loading={loading} size="lg">
            {t("sign_in_with_google")}
          </Button>
        </FadeUp>

        {/* ── Footer tagline ── */}
        <FadeUp delay={800}>
          <Text className="text-xs text-muted-foreground text-center mt-8 opacity-60">
            {t("login_footer")}
          </Text>
        </FadeUp>
      </View>
    </View>
  );
}
