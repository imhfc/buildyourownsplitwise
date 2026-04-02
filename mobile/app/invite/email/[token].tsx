import { useCallback, useState } from "react";
import { View, ActivityIndicator } from "react-native";
import { useLocalSearchParams, router, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import { EnvelopeSimple, UsersThree, CaretLeft, WarningCircle, CheckCircle } from "phosphor-react-native";
import { inviteAPI } from "../../../services/api";
import { useAuthStore } from "../../../stores/auth";
import { Text, H1, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Card, CardContent } from "~/components/ui/card";

interface EmailInviteInfo {
  id: string;
  group_id: string;
  group_name: string;
  group_description: string | null;
  inviter_name: string;
  member_count: number;
}

export default function EmailInviteScreen() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const setPendingInviteToken = useAuthStore((s) => s.setPendingInviteToken);

  const [info, setInfo] = useState<EmailInviteInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [responding, setResponding] = useState(false);
  const [error, setError] = useState("");
  const [joinedGroupId, setJoinedGroupId] = useState<string | null>(null);
  const [declined, setDeclined] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (!hasHydrated || !token) return;

      if (!isAuthenticated) {
        setPendingInviteToken(`email:${token}`);
        router.replace("/(auth)/login");
        return;
      }

      setLoading(true);
      setError("");
      inviteAPI
        .getEmailInviteByToken(token)
        .then((res) => setInfo(res.data))
        .catch((e: any) => {
          const status = e.response?.status;
          const detail = e.response?.data?.detail || t("unknown_error");
          if (status === 404) {
            setError(t("invalid_invite"));
          } else if (status === 403) {
            setError(t("email_invite_not_for_you"));
          } else {
            setError(detail);
          }
        })
        .finally(() => setLoading(false));
    }, [hasHydrated, isAuthenticated, token])
  );

  const handleRespond = async (action: "accept" | "decline") => {
    if (!token) return;
    setResponding(true);
    setError("");
    try {
      const res = await inviteAPI.respondToEmailInviteByToken(token, action);
      if (action === "accept") {
        setJoinedGroupId(res.data.group_id);
      } else {
        setDeclined(true);
      }
    } catch (e: any) {
      const status = e.response?.status;
      if (status === 409) {
        // Already a member or already responded
        if (info) setJoinedGroupId(info.group_id);
      } else if (status === 403) {
        setError(t("email_invite_not_for_you"));
      } else if (status === 404) {
        setError(t("invalid_invite"));
      } else {
        setError(e.response?.data?.detail || t("unknown_error"));
      }
    } finally {
      setResponding(false);
    }
  };

  const goToGroup = () => {
    if (joinedGroupId) {
      router.replace(`/group/${joinedGroupId}`);
    }
  };

  const goBack = () => {
    router.canGoBack() ? router.back() : router.replace("/(tabs)");
  };

  if (!hasHydrated || loading) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View className="flex-1 bg-background">
      <View className="flex-row items-center px-3 pt-3 pb-1">
        <Button variant="ghost" size="sm" onPress={goBack}>
          <View className="flex-row items-center">
            <CaretLeft size={20} color="hsl(var(--primary))" weight="regular" />
            <Text className="text-primary">{t("back")}</Text>
          </View>
        </Button>
      </View>

      <View className="flex-1 justify-center px-6">
        {error ? (
          <View className="items-center gap-4">
            <WarningCircle size={48} color="hsl(0 84.2% 60.2%)" weight="regular" />
            <Text className="text-lg font-semibold text-center">{t("invalid_invite")}</Text>
            <Muted className="text-center">{error}</Muted>
            <Button onPress={goBack} className="mt-4">{t("back_to_home")}</Button>
          </View>
        ) : joinedGroupId ? (
          <View className="items-center gap-4">
            <CheckCircle size={48} color="hsl(var(--primary))" weight="regular" />
            <Text className="text-lg font-semibold text-center">{t("joined_successfully")}</Text>
            {info && <Muted className="text-center">{info.group_name}</Muted>}
            <Button onPress={goToGroup} className="mt-4">{t("go_to_group")}</Button>
          </View>
        ) : declined ? (
          <View className="items-center gap-4">
            <CheckCircle size={48} color="hsl(var(--muted-foreground))" weight="regular" />
            <Text className="text-lg font-semibold text-center">{t("invitation_declined")}</Text>
            <Button onPress={goBack} className="mt-4">{t("back_to_home")}</Button>
          </View>
        ) : info ? (
          <View className="items-center gap-6">
            <H1 className="text-primary text-center">{t("email_invite_title")}</H1>

            <Card className="w-full">
              <CardContent className="p-5 gap-3">
                <View className="flex-row items-center gap-3">
                  <View className="h-12 w-12 rounded-full bg-primary/10 items-center justify-center">
                    <UsersThree size={24} color="hsl(var(--primary))" weight="regular" />
                  </View>
                  <View className="flex-1">
                    <Text className="text-lg font-bold">{info.group_name}</Text>
                    {info.group_description ? (
                      <Muted numberOfLines={2}>{info.group_description}</Muted>
                    ) : null}
                  </View>
                </View>
                <View className="flex-row items-center gap-2">
                  <EnvelopeSimple size={16} color="hsl(var(--muted-foreground))" weight="regular" />
                  <Muted>{t("invited_by", { name: info.inviter_name })}</Muted>
                </View>
                <Muted>
                  {t("member_count", { count: info.member_count })}
                </Muted>
              </CardContent>
            </Card>

            <View className="w-full gap-3">
              <Button onPress={() => handleRespond("accept")} loading={responding} size="lg" className="w-full">
                {t("accept_invitation")}
              </Button>
              <Button
                variant="outline"
                onPress={() => handleRespond("decline")}
                disabled={responding}
                size="lg"
                className="w-full"
              >
                {t("decline_invitation")}
              </Button>
            </View>
          </View>
        ) : null}
      </View>
    </View>
  );
}
