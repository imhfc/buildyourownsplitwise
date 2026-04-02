import { useState, useCallback } from "react";
import {
  View,
  Modal,
  Pressable,
  Image,
  ScrollView,
  ActivityIndicator,
  TextInput,
  FlatList,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { X, MagnifyingGlass, ImageSquare, Camera } from "phosphor-react-native";
import { useTranslation } from "react-i18next";
import { Text, Muted } from "./text";
import { Button } from "./button";
import { cn } from "~/lib/utils";

// Unsplash API (free tier: 50 req/hr)
const UNSPLASH_API = "https://api.unsplash.com/search/photos";

// 預設圖庫：硬編碼 Unsplash 圖片（不耗 API quota）
// 使用 Unsplash Source 的固定圖片，免費且不需 API key
const PRESET_CATEGORIES = [
  {
    key: "travel",
    images: [
      "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80",
      "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&q=80",
    ],
  },
  {
    key: "food",
    images: [
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80",
      "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80",
    ],
  },
  {
    key: "party",
    images: [
      "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=800&q=80",
      "https://images.unsplash.com/photo-1496843916299-590492c751f4?w=800&q=80",
    ],
  },
  {
    key: "office",
    images: [
      "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
      "https://images.unsplash.com/photo-1497215842964-222b430dc094?w=800&q=80",
    ],
  },
  {
    key: "nature",
    images: [
      "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80",
      "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&q=80",
    ],
  },
  {
    key: "city",
    images: [
      "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=80",
      "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800&q=80",
    ],
  },
] as const;

interface UnsplashPhoto {
  id: string;
  urls: { small: string; regular: string };
  user: { name: string; links: { html: string } };
}

interface CoverImagePickerProps {
  value: string;
  onSelect: (url: string | null) => void;
  label?: string;
}

export function CoverImagePicker({ value, onSelect, label }: CoverImagePickerProps) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"presets" | "search">("presets");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UnsplashPhoto[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);

  const unsplashKey = process.env.EXPO_PUBLIC_UNSPLASH_ACCESS_KEY ?? "";

  const handleSearch = useCallback(async () => {
    const trimmed = query.trim();
    if (!trimmed || !unsplashKey) return;
    setSearching(true);
    setSearchError(null);
    try {
      const res = await fetch(
        `${UNSPLASH_API}?query=${encodeURIComponent(trimmed)}&per_page=20&orientation=landscape`,
        { headers: { Authorization: `Client-ID ${unsplashKey}` } }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data.results ?? []);
    } catch {
      setSearchError(t("cover_search_failed"));
    } finally {
      setSearching(false);
    }
  }, [query, unsplashKey, t]);

  const handleConfirm = useCallback(() => {
    onSelect(selectedUrl);
    setVisible(false);
    setSelectedUrl(null);
    setQuery("");
    setResults([]);
  }, [selectedUrl, onSelect]);

  const handleRemove = useCallback(() => {
    onSelect(null);
    setVisible(false);
    setSelectedUrl(null);
  }, [onSelect]);

  const openPicker = useCallback(() => {
    setSelectedUrl(value || null);
    setActiveTab("presets");
    setVisible(true);
  }, [value]);

  const renderImageItem = useCallback(
    (url: string, attribution?: { name: string; link: string }) => (
      <Pressable
        key={url}
        onPress={() => setSelectedUrl(url)}
        className={cn(
          "rounded-lg overflow-hidden border-2 m-1",
          selectedUrl === url ? "border-primary" : "border-transparent"
        )}
        style={{ width: "47%", aspectRatio: 16 / 9 }}
      >
        <Image
          source={{ uri: url }}
          style={{ width: "100%", height: "100%" }}
          resizeMode="cover"
        />
        {attribution ? (
          <View className="absolute bottom-0 left-0 right-0 bg-black/40 px-1 py-0.5">
            <Text className="text-white text-[9px]" numberOfLines={1}>
              {attribution.name}
            </Text>
          </View>
        ) : null}
      </Pressable>
    ),
    [selectedUrl]
  );

  return (
    <View className="gap-1.5">
      {label ? (
        <Text className="text-sm font-medium text-foreground">{label}</Text>
      ) : null}

      <Pressable
        onPress={openPicker}
        className="h-24 rounded-lg border border-input bg-background overflow-hidden items-center justify-center"
      >
        {value ? (
          <Image
            source={{ uri: value }}
            style={{ width: "100%", height: "100%" }}
            resizeMode="cover"
          />
        ) : (
          <View className="items-center gap-1">
            <ImageSquare size={28} color="hsl(240 3.8% 46.1%)" />
            <Muted className="text-xs">{t("cover_tap_to_select")}</Muted>
          </View>
        )}
      </Pressable>

      <Modal
        visible={visible}
        transparent
        animationType="slide"
        onRequestClose={() => setVisible(false)}
      >
        <KeyboardAvoidingView
          className="flex-1 bg-black/50 justify-end"
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View
            className="bg-background rounded-t-2xl"
            style={{ maxHeight: "85%", paddingBottom: Platform.OS === "ios" ? 34 : 16 }}
          >
            {/* Header */}
            <View className="px-5 pt-4 pb-2">
              <View className="items-center mb-3">
                <View className="h-1 w-10 rounded-full bg-muted-foreground/30" />
              </View>
              <View className="flex-row items-center justify-between mb-3">
                <Text className="text-lg font-semibold text-foreground">
                  {t("cover_select_image")}
                </Text>
                <Pressable onPress={() => setVisible(false)}>
                  <X size={24} color="hsl(240 3.8% 46.1%)" />
                </Pressable>
              </View>

              {/* Tabs */}
              <View className="flex-row gap-2 mb-3">
                <Pressable
                  onPress={() => setActiveTab("presets")}
                  className={cn(
                    "flex-1 py-2 rounded-lg items-center",
                    activeTab === "presets" ? "bg-primary" : "bg-muted"
                  )}
                >
                  <Text
                    className={cn(
                      "text-sm font-medium",
                      activeTab === "presets"
                        ? "text-primary-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {t("cover_presets")}
                  </Text>
                </Pressable>
                {unsplashKey ? (
                  <Pressable
                    onPress={() => setActiveTab("search")}
                    className={cn(
                      "flex-1 py-2 rounded-lg items-center",
                      activeTab === "search" ? "bg-primary" : "bg-muted"
                    )}
                  >
                    <Text
                      className={cn(
                        "text-sm font-medium",
                        activeTab === "search"
                          ? "text-primary-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      {t("cover_search")}
                    </Text>
                  </Pressable>
                ) : null}
              </View>
            </View>

            {/* Content */}
            <ScrollView className="px-4" keyboardShouldPersistTaps="handled">
              {activeTab === "presets" ? (
                <View>
                  {PRESET_CATEGORIES.map((cat) => (
                    <View key={cat.key} className="mb-4">
                      <Text className="text-sm font-medium text-muted-foreground mb-2 px-1">
                        {t(`cover_cat_${cat.key}`)}
                      </Text>
                      <View className="flex-row flex-wrap justify-between">
                        {cat.images.map((url) => renderImageItem(url))}
                      </View>
                    </View>
                  ))}
                </View>
              ) : (
                <View>
                  {/* Search bar */}
                  <View className="flex-row gap-2 mb-3">
                    <View className="flex-1 flex-row items-center h-10 rounded-lg border border-input bg-background px-3">
                      <MagnifyingGlass size={18} color="hsl(240 3.8% 46.1%)" />
                      <TextInput
                        className="flex-1 ml-2 text-sm text-foreground"
                        placeholder={t("cover_search_placeholder")}
                        placeholderTextColor="hsl(240 3.8% 46.1%)"
                        value={query}
                        onChangeText={setQuery}
                        onSubmitEditing={handleSearch}
                        returnKeyType="search"
                        autoCapitalize="none"
                      />
                    </View>
                    <Button
                      onPress={handleSearch}
                      disabled={searching || !query.trim()}
                      size="sm"
                      className="h-10 px-4"
                    >
                      {t("cover_search_btn")}
                    </Button>
                  </View>

                  {searching ? (
                    <View className="items-center py-8">
                      <ActivityIndicator />
                    </View>
                  ) : searchError ? (
                    <Text className="text-sm text-destructive text-center py-4">
                      {searchError}
                    </Text>
                  ) : results.length > 0 ? (
                    <View className="flex-row flex-wrap justify-between">
                      {results.map((photo) =>
                        renderImageItem(photo.urls.regular, {
                          name: photo.user.name,
                          link: photo.user.links.html,
                        })
                      )}
                    </View>
                  ) : query.trim() ? (
                    <Muted className="text-center py-4">{t("no_results")}</Muted>
                  ) : (
                    <Muted className="text-center py-4">
                      {t("cover_search_hint")}
                    </Muted>
                  )}

                  {/* Unsplash attribution */}
                  <Muted className="text-[10px] text-center mt-2 mb-4">
                    Photos by Unsplash
                  </Muted>
                </View>
              )}
            </ScrollView>

            {/* Preview + Actions */}
            {selectedUrl ? (
              <View className="px-5 pt-3 border-t border-border">
                <View className="rounded-lg overflow-hidden mb-3" style={{ height: 80 }}>
                  <Image
                    source={{ uri: selectedUrl }}
                    style={{ width: "100%", height: "100%" }}
                    resizeMode="cover"
                  />
                </View>
                <View className="flex-row gap-2">
                  {value ? (
                    <Button
                      variant="destructive"
                      onPress={handleRemove}
                      className="flex-1"
                      size="sm"
                    >
                      {t("cover_remove")}
                    </Button>
                  ) : null}
                  <Button onPress={handleConfirm} className="flex-1" size="sm">
                    {t("confirm")}
                  </Button>
                </View>
              </View>
            ) : value ? (
              <View className="px-5 pt-3 border-t border-border">
                <Button variant="destructive" onPress={handleRemove} size="sm">
                  {t("cover_remove")}
                </Button>
              </View>
            ) : null}
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
