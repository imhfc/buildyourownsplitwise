import { useCallback, useEffect, useState } from "react";
import {
  View,
  FlatList,
  RefreshControl,
  Modal,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  UserPlus,
  UsersThree,
  X,
  Clock,
  Check,
  XCircle,
  MagnifyingGlass,
  UserMinus,
} from "phosphor-react-native";
import { friendsAPI } from "../../services/api";
import { Text, H3, Muted } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Card, CardContent } from "~/components/ui/card";
import { EmptyState } from "~/components/ui/empty-state";
import { SegmentedTabs } from "~/components/ui/tabs";
import { FAB } from "~/components/ui/fab";
import { Avatar } from "~/components/ui/avatar";
import { useThemeClassName } from "~/lib/theme";
import { addNotificationReceivedCallback } from "~/lib/notifications";

interface FriendUser {
  id: string;
  email: string | null;
  display_name: string;
  avatar_url: string | null;
}

interface FriendItem {
  friend: FriendUser;
  friendship_id: string;
  since: string;
}

interface PendingRequest {
  id: string;
  user: FriendUser;
  status: string;
  created_at: string;
}

interface SearchResult {
  user: FriendUser;
  is_friend: boolean;
  has_pending_request: boolean;
}

type TabValue = "friends" | "pending";

export default function FriendsScreen() {
  const { t } = useTranslation();
  const themeClass = useThemeClassName();
  const [tab, setTab] = useState<TabValue>("friends");
  const [friends, setFriends] = useState<FriendItem[]>([]);
  const [pending, setPending] = useState<PendingRequest[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  // Add friend modal
  const [showAdd, setShowAdd] = useState(false);
  const [searchEmail, setSearchEmail] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [sendingTo, setSendingTo] = useState<string | null>(null);
  const [sentEmails, setSentEmails] = useState<Set<string>>(new Set());
  const [searchError, setSearchError] = useState<string | null>(null);

  // Remove friend modal
  const [removeTarget, setRemoveTarget] = useState<FriendItem | null>(null);
  const [removing, setRemoving] = useState(false);

  // Respond to request loading
  const [respondingTo, setRespondingTo] = useState<string | null>(null);

  const fetchFriends = useCallback(async () => {
    try {
      const res = await friendsAPI.list();
      setFriends(res.data);
    } catch {
      // silent
    }
  }, []);

  const fetchPending = useCallback(async () => {
    try {
      const res = await friendsAPI.getRequests();
      setPending(res.data);
    } catch {
      // silent
    }
  }, []);

  const fetchAll = useCallback(async () => {
    await Promise.all([fetchFriends(), fetchPending()]);
  }, [fetchFriends, fetchPending]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      fetchAll().finally(() => setLoading(false));
    }, [fetchAll])
  );

  // 收到推播時即時刷新好友列表
  useEffect(() => {
    return addNotificationReceivedCallback(() => {
      fetchAll();
    });
  }, [fetchAll]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchAll();
    setRefreshing(false);
  };

  // Search users
  const handleSearch = async () => {
    const trimmed = searchEmail.trim();
    if (!trimmed) return;
    setSearching(true);
    setSearchError(null);
    setSearchResults([]);
    try {
      const res = await friendsAPI.search(trimmed);
      setSearchResults(res.data);
      if (res.data.length === 0) {
        setSearchError(t("no_search_results"));
      }
    } catch {
      setSearchError(t("unknown_error"));
    } finally {
      setSearching(false);
    }
  };

  // Send friend request
  const handleSendRequest = async (email: string) => {
    setSendingTo(email);
    try {
      await friendsAPI.sendRequest(email);
      setSentEmails((prev) => new Set(prev).add(email));
      await fetchPending();
    } catch {
      // silent — could show inline error
    } finally {
      setSendingTo(null);
    }
  };

  // Respond to request
  const handleRespond = async (id: string, action: "accept" | "reject") => {
    setRespondingTo(id);
    try {
      await friendsAPI.handleRequest(id, action);
      await fetchAll();
    } catch {
      // silent
    } finally {
      setRespondingTo(null);
    }
  };

  // Remove friend
  const handleRemove = async () => {
    if (!removeTarget) return;
    setRemoving(true);
    try {
      await friendsAPI.removeFriend(removeTarget.friendship_id);
      setRemoveTarget(null);
      await fetchFriends();
    } catch {
      // silent
    } finally {
      setRemoving(false);
    }
  };

  const closeAddModal = () => {
    setShowAdd(false);
    setSearchEmail("");
    setSearchResults([]);
    setSearchError(null);
    setSentEmails(new Set());
  };

  const tabs = [
    { value: "friends", label: t("friends_list") },
    { value: "pending", label: t("pending_requests") },
  ];

  const renderAvatar = (name: string, avatarUrl?: string | null, index?: number) => (
    <Avatar name={name} avatarUrl={avatarUrl} index={index} size="md" />
  );

  const renderFriendItem = ({ item, index }: { item: FriendItem; index: number }) => (
    <Card className="mb-3">
      <CardContent className="flex-row items-center p-4 gap-3">
        {renderAvatar(item.friend.display_name, item.friend.avatar_url, index)}
        <View className="flex-1">
          <Text className="text-base font-medium">{item.friend.display_name}</Text>
          {item.friend.email ? (
            <Muted className="text-xs">{item.friend.email}</Muted>
          ) : null}
        </View>
        <Pressable
          onPress={() => setRemoveTarget(item)}
          className="p-2"
          hitSlop={8}
        >
          <UserMinus size={20} color="hsl(0 84.2% 60.2%)" />
        </Pressable>
      </CardContent>
    </Card>
  );

  const renderPendingItem = ({ item }: { item: PendingRequest }) => (
    <Card className="mb-3">
      <CardContent className="flex-row items-center p-4 gap-3">
        {renderAvatar(item.user.display_name, item.user.avatar_url)}
        <View className="flex-1">
          <Text className="text-sm font-medium">
            {t("friend_request_from", { name: item.user.display_name })}
          </Text>
          {item.user.email ? (
            <Muted className="text-xs">{item.user.email}</Muted>
          ) : null}
        </View>
        <View className="flex-row gap-2">
          <Pressable
            onPress={() => handleRespond(item.id, "accept")}
            disabled={respondingTo === item.id}
            className="h-9 w-9 rounded-full bg-income/15 items-center justify-center"
          >
            {respondingTo === item.id ? (
              <ActivityIndicator size="small" color="#22c55e" />
            ) : (
              <Check size={18} color="#22c55e" />
            )}
          </Pressable>
          <Pressable
            onPress={() => handleRespond(item.id, "reject")}
            disabled={respondingTo === item.id}
            className="h-9 w-9 rounded-full bg-destructive/15 items-center justify-center"
          >
            <XCircle size={18} color="#ef4444" />
          </Pressable>
        </View>
      </CardContent>
    </Card>
  );

  const renderSearchResult = ({ item }: { item: SearchResult }) => {
    const email = item.user.email ?? "";
    const isSent = sentEmails.has(email);
    const isFriend = item.is_friend;
    const isPending = item.has_pending_request;
    const isSending = sendingTo === email;

    let statusLabel: string | null = null;
    if (isFriend) statusLabel = t("already_friends");
    else if (isPending || isSent) statusLabel = t("request_pending");

    return (
      <View className="flex-row items-center py-3 gap-3">
        {renderAvatar(item.user.display_name, item.user.avatar_url)}
        <View className="flex-1">
          <Text className="text-sm font-medium">{item.user.display_name}</Text>
          {email ? <Muted className="text-xs">{email}</Muted> : null}
        </View>
        {statusLabel ? (
          <Muted className="text-xs">{statusLabel}</Muted>
        ) : (
          <Button
            size="sm"
            onPress={() => handleSendRequest(email)}
            loading={isSending}
            disabled={isSending}
          >
            {t("send_request")}
          </Button>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View className="flex-1 bg-background">
      <View className="px-5 pt-4 pb-2">
        <SegmentedTabs
          tabs={tabs}
          value={tab}
          onValueChange={(v) => setTab(v as TabValue)}
        />
      </View>

      {tab === "friends" ? (
        <FlatList
          data={friends}
          keyExtractor={(item) => item.friendship_id}
          renderItem={renderFriendItem}
          contentContainerStyle={
            friends.length === 0 ? { flex: 1, padding: 20 } : { padding: 20 }
          }
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <EmptyState
              icon={UsersThree}
              title={t("no_friends")}
              description={t("no_friends_desc")}
              actionLabel={t("add_friend")}
              onAction={() => setShowAdd(true)}
            />
          }
        />
      ) : (
        <FlatList
          data={pending}
          keyExtractor={(item) => item.id}
          renderItem={renderPendingItem}
          contentContainerStyle={
            pending.length === 0 ? { flex: 1, padding: 20 } : { padding: 20 }
          }
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <EmptyState icon={Clock} title={t("no_pending")} />
          }
        />
      )}

      <FAB onPress={() => setShowAdd(true)} />

      {/* Add Friend Modal */}
      <Modal
        visible={showAdd}
        transparent
        animationType="slide"
        onRequestClose={closeAddModal}
      >
        <View className={`flex-1 ${themeClass}`}>
        <KeyboardAvoidingView
          className="flex-1 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View className="flex-1 justify-end bg-black/50">
            <View className="bg-background rounded-t-2xl px-5 pb-10 pt-4 max-h-[80%]">
              <View className="items-center mb-4">
                <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
              </View>

              <View className="flex-row items-center justify-between mb-6">
                <H3>{t("add_friend")}</H3>
                <Pressable onPress={closeAddModal}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              <View className="flex-row gap-2 mb-4">
                <View className="flex-1">
                  <Input
                    placeholder={t("search_by_email")}
                    value={searchEmail}
                    onChangeText={setSearchEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                  />
                </View>
                <Button
                  size="default"
                  onPress={handleSearch}
                  loading={searching}
                  disabled={searching || !searchEmail.trim()}
                  className="self-start"
                >
                  <MagnifyingGlass size={18} color="white" weight="regular" />
                </Button>
              </View>

              {searchError ? (
                <Muted className="text-center py-4">{searchError}</Muted>
              ) : null}

              <FlatList
                data={searchResults}
                keyExtractor={(item) => item.user.id}
                renderItem={renderSearchResult}
                keyboardShouldPersistTaps="handled"
                ListEmptyComponent={
                  !searching && searchResults.length === 0 && !searchError ? (
                    <Muted className="text-center py-4">
                      {t("search_by_email")}
                    </Muted>
                  ) : null
                }
              />
            </View>
          </View>
        </KeyboardAvoidingView>
        </View>
      </Modal>

      {/* Remove Friend Confirm Modal */}
      <Modal
        visible={!!removeTarget}
        transparent
        animationType="fade"
        onRequestClose={() => setRemoveTarget(null)}
      >
        <View className={`flex-1 ${themeClass}`}>
        <View className="flex-1 justify-center items-center bg-black/50 px-6">
          <View className="bg-background rounded-xl p-6 w-full max-w-sm gap-4">
            <H3>{t("remove_friend")}</H3>
            <Text className="text-muted-foreground">
              {t("remove_friend_confirm")}
            </Text>
            <View className="flex-row gap-3 justify-end">
              <Button
                variant="outline"
                onPress={() => setRemoveTarget(null)}
                disabled={removing}
              >
                {t("cancel")}
              </Button>
              <Button
                variant="destructive"
                onPress={handleRemove}
                loading={removing}
                disabled={removing}
              >
                {t("confirm")}
              </Button>
            </View>
          </View>
        </View>
        </View>
      </Modal>
    </View>
  );
}
