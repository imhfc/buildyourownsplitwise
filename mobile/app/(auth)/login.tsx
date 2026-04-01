import { useState, useEffect, useRef } from "react";
import {
  View,
  Platform,
  Animated,
  Easing,
  StyleSheet,
  type DimensionValue,
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
   Floating decorative orb
   ──────────────────────────────────────────── */

function Orb({
  size,
  top,
  left,
  delay,
  range,
  speed,
  targetOpacity,
}: {
  size: number;
  top: DimensionValue;
  left: DimensionValue;
  delay: number;
  range: number;
  speed: number;
  targetOpacity: number;
}) {
  const ty = useRef(new Animated.Value(0)).current;
  const fade = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fade, {
      toValue: targetOpacity,
      duration: 1200,
      delay,
      useNativeDriver: USE_NATIVE,
    }).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(ty, {
          toValue: -range,
          duration: speed,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: USE_NATIVE,
        }),
        Animated.timing(ty, {
          toValue: range,
          duration: speed,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: USE_NATIVE,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        position: "absolute",
        top,
        left,
        opacity: fade,
        transform: [{ translateY: ty }],
      }}
    >
      <View
        className="bg-primary rounded-full"
        style={{ width: size, height: size }}
      />
    </Animated.View>
  );
}

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
          router.replace(`/join/${pending}`);
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
      setError("Google Client ID not configured");
      return;
    }
    window.location.href = buildGoogleOAuthUrl();
  };

  return (
    <View className="flex-1 bg-background">
      {/* Decorative floating orbs */}
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <Orb size={140} top="4%"  left="65%" delay={0}   range={18} speed={3200} targetOpacity={0.07} />
        <Orb size={90}  top="15%" left="5%"  delay={400} range={12} speed={2800} targetOpacity={0.06} />
        <Orb size={180} top="50%" left="75%" delay={700} range={14} speed={3600} targetOpacity={0.04} />
        <Orb size={70}  top="70%" left="3%"  delay={200} range={10} speed={2400} targetOpacity={0.08} />
        <Orb size={110} top="35%" left="85%" delay={500} range={16} speed={3000} targetOpacity={0.05} />
        <Orb size={50}  top="85%" left="50%" delay={300} range={8}  speed={2600} targetOpacity={0.06} />
      </View>

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
            <Text className="text-5xl font-extrabold text-primary tracking-widest">
              {t("app_name")}
            </Text>

            {/* Decorative line */}
            <View className="bg-primary/20 rounded-full mt-4 mb-3" style={{ width: 48, height: 3 }} />

            {/* Subtitle */}
            <Text className="text-base text-muted-foreground text-center px-4 leading-6">
              {t("app_subtitle")}
            </Text>
          </View>
        </Animated.View>

        {/* ── Error banner ── */}
        {error ? (
          <FadeUp delay={0}>
            <View className="border border-destructive rounded-xl px-4 py-3 mb-4">
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
