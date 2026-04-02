import { useState } from "react";
import { View, Modal, Pressable, KeyboardAvoidingView, Platform } from "react-native";
import { useTranslation } from "react-i18next";
import { X, Copy, Share2, RefreshCw, Trash2 } from "lucide-react-native";
import { groupsAPI } from "../services/api";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { useThemeClassName } from "~/lib/theme";

interface InviteShareModalProps {
  visible: boolean;
  onClose: () => void;
  groupId: string;
  groupName: string;
  isAdmin: boolean;
}

export function InviteShareModal({ visible, onClose, groupId, groupName, isAdmin }: InviteShareModalProps) {
  const { t } = useTranslation();
  const themeClass = useThemeClassName();

  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const inviteUrl = inviteToken
    ? `${Platform.OS === "web" ? window.location.origin : "https://byosw.duckdns.org"}/join/${inviteToken}`
    : "";

  const fetchInvite = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await groupsAPI.createInvite(groupId);
      setInviteToken(res.data.invite_token);
    } catch (e: any) {
      setError(e.response?.data?.detail || t("unknown_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    if (!inviteToken) {
      fetchInvite();
    }
  };

  const handleCopy = async () => {
    if (!inviteUrl) return;
    try {
      if (Platform.OS === "web" && navigator.clipboard) {
        await navigator.clipboard.writeText(inviteUrl);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError(t("unknown_error"));
    }
  };

  const handleShareToLine = () => {
    if (!inviteUrl) return;
    const message = t("invite_message", { groupName, url: inviteUrl });
    const lineUrl = `https://line.me/R/share?text=${encodeURIComponent(message)}`;
    if (Platform.OS === "web") {
      window.open(lineUrl, "_blank");
    }
  };

  const handleRegenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await groupsAPI.regenerateInvite(groupId);
      setInviteToken(res.data.invite_token);
    } catch (e: any) {
      setError(e.response?.data?.detail || t("unknown_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async () => {
    setLoading(true);
    setError("");
    try {
      await groupsAPI.revokeInvite(groupId);
      setInviteToken(null);
      onClose();
    } catch (e: any) {
      setError(e.response?.data?.detail || t("unknown_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
      onShow={handleOpen}
    >
      <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View className="flex-1 justify-end bg-black/50">
            <View className="bg-background rounded-t-2xl px-5 pb-10 pt-4">
              <View className="items-center mb-4">
                <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
              </View>

              <View className="flex-row items-center justify-between mb-6">
                <H3>{t("invite_link")}</H3>
                <Pressable onPress={onClose}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              {loading && !inviteToken ? (
                <View className="items-center py-8">
                  <Muted>{t("loading")}</Muted>
                </View>
              ) : inviteToken ? (
                <View className="gap-4">
                  <Input
                    value={inviteUrl}
                    editable={false}
                    label={t("invite_link")}
                  />

                  <Button onPress={handleCopy} variant="outline">
                    <View className="flex-row items-center gap-2">
                      <Copy size={16} color="hsl(var(--foreground))" />
                      <Text>{copied ? t("link_copied") : t("copy_link")}</Text>
                    </View>
                  </Button>

                  <Button onPress={handleShareToLine}>
                    <View className="flex-row items-center gap-2">
                      <Share2 size={16} color="hsl(var(--primary-foreground))" />
                      <Text className="text-primary-foreground font-semibold">{t("share_to_line")}</Text>
                    </View>
                  </Button>

                  {isAdmin && (
                    <View className="flex-row gap-3 mt-2">
                      <Button
                        onPress={handleRegenerate}
                        variant="outline"
                        loading={loading}
                        className="flex-1"
                      >
                        <View className="flex-row items-center gap-2">
                          <RefreshCw size={14} color="hsl(var(--foreground))" />
                          <Text className="text-sm">{t("regenerate_invite")}</Text>
                        </View>
                      </Button>
                      <Button
                        onPress={handleRevoke}
                        variant="destructive"
                        loading={loading}
                        className="flex-1"
                      >
                        <View className="flex-row items-center gap-2">
                          <Trash2 size={14} color="#fff" />
                          <Text className="text-destructive-foreground text-sm">{t("revoke_invite")}</Text>
                        </View>
                      </Button>
                    </View>
                  )}

                  {error ? (
                    <Text className="text-sm text-destructive">{error}</Text>
                  ) : null}
                </View>
              ) : error ? (
                <View className="gap-4">
                  <Text className="text-destructive">{error}</Text>
                  <Button onPress={fetchInvite}>{t("retry")}</Button>
                </View>
              ) : null}
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}
