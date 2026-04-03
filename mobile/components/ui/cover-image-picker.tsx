import { useState, useCallback, useRef } from "react";
import {
  View,
  Modal,
  Pressable,
  Image,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { X, ImageSquare, ArrowsClockwise } from "phosphor-react-native";
import { useTranslation } from "react-i18next";
import { Text, Muted } from "./text";
import { Button } from "./button";
import { cn } from "~/lib/utils";

/** 每個分類每次顯示幾張 */
const IMAGES_PER_PAGE = 8;

/**
 * 不重複分頁抽取器：將陣列 shuffle 後依序取 n 張，
 * 全部遍歷過一輪後才重新 shuffle。
 */
class ShuffledPager<T> {
  private pool: T[] = [];
  private cursor = 0;

  constructor(private readonly source: readonly T[]) {
    this.reshuffle();
  }

  private reshuffle() {
    this.pool = [...this.source].sort(() => Math.random() - 0.5);
    this.cursor = 0;
  }

  next(n: number): T[] {
    const result: T[] = [];
    for (let i = 0; i < n; i++) {
      if (this.cursor >= this.pool.length) {
        this.reshuffle();
      }
      result.push(this.pool[this.cursor++]);
    }
    return result;
  }
}

// 精選圖庫：Unsplash 靜態 URL（不需要 API key）
const PRESET_CATEGORIES = [
  {
    key: "travel",
    images: [
      "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80",
      "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&q=80",
      "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80",
      "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800&q=80",
      "https://images.unsplash.com/photo-1530789253388-582c481c54b0?w=800&q=80",
      "https://images.unsplash.com/photo-1500835556837-99ac94a94552?w=800&q=80",
      "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?w=800&q=80",
      "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&q=80",
      "https://images.unsplash.com/photo-1539635278303-d4002c07eae3?w=800&q=80",
      "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=800&q=80",
      "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&q=80",
      "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=800&q=80",
      "https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=800&q=80",
      "https://images.unsplash.com/photo-1528164344705-47542687000d?w=800&q=80",
      "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?w=800&q=80",
      "https://images.unsplash.com/photo-1433838552652-f9a46b332c40?w=800&q=80",
      "https://images.unsplash.com/photo-1502003148287-a82ef80a6b2c?w=800&q=80",
      "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=800&q=80",
      "https://images.unsplash.com/photo-1527631746610-bca00a040d60?w=800&q=80",
      "https://images.unsplash.com/photo-1543785734-4b6e564642f8?w=800&q=80",
    ],
  },
  {
    key: "food",
    images: [
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80",
      "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80",
      "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800&q=80",
      "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800&q=80",
      "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&q=80",
      "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80",
      "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?w=800&q=80",
      "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=800&q=80",
      "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=800&q=80",
      "https://images.unsplash.com/photo-1432139555190-58524dae6a55?w=800&q=80",
      "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80",
      "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80",
      "https://images.unsplash.com/photo-1493770348161-369560ae357d?w=800&q=80",
      "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800&q=80",
      "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=800&q=80",
      "https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=800&q=80",
      "https://images.unsplash.com/photo-1551218808-94e220e084d2?w=800&q=80",
      "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=800&q=80",
      "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=800&q=80",
      "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&q=80",
    ],
  },
  {
    key: "party",
    images: [
      "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=800&q=80",
      "https://images.unsplash.com/photo-1496843916299-590492c751f4?w=800&q=80",
      "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=800&q=80",
      "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&q=80",
      "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&q=80",
      "https://images.unsplash.com/photo-1504196606672-aef5c9cefc92?w=800&q=80",
      "https://images.unsplash.com/photo-1528495612343-9ca9f4a4de28?w=800&q=80",
      "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=800&q=80",
      "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800&q=80",
      "https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=800&q=80",
      "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800&q=80",
      "https://images.unsplash.com/photo-1429962714451-bb934ecdc4ec?w=800&q=80",
      "https://images.unsplash.com/photo-1485872299829-c44683349bc7?w=800&q=80",
      "https://images.unsplash.com/photo-1509924603848-aca5e5f276d7?w=800&q=80",
      "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800&q=80",
      "https://images.unsplash.com/photo-1507608616759-54f48f0af0ee?w=800&q=80",
      "https://images.unsplash.com/photo-1545128485-c400e7702796?w=800&q=80",
      "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=800&q=80",
      "https://images.unsplash.com/photo-1546171753-97d7676e4602?w=800&q=80",
      "https://images.unsplash.com/photo-1543807535-eceef0bc6599?w=800&q=80",
    ],
  },
  {
    key: "office",
    images: [
      "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
      "https://images.unsplash.com/photo-1497215842964-222b430dc094?w=800&q=80",
      "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80",
      "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800&q=80",
      "https://images.unsplash.com/photo-1462826303086-329426d1aef5?w=800&q=80",
      "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800&q=80",
      "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=800&q=80",
      "https://images.unsplash.com/photo-1554469384-e58fac16e23a?w=800&q=80",
      "https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?w=800&q=80",
      "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=800&q=80",
      "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=800&q=80",
      "https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=800&q=80",
      "https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=800&q=80",
      "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80",
      "https://images.unsplash.com/photo-1564069114553-7215e1ff1890?w=800&q=80",
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80",
      "https://images.unsplash.com/photo-1556761175-4b46a572b786?w=800&q=80",
      "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=800&q=80",
      "https://images.unsplash.com/photo-1531973576160-7125cd663d86?w=800&q=80",
      "https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&q=80",
    ],
  },
  {
    key: "nature",
    images: [
      "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80",
      "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&q=80",
      "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=800&q=80",
      "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=800&q=80",
      "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=800&q=80",
      "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=800&q=80",
      "https://images.unsplash.com/photo-1465795145685-e190bcd4e4e6?w=800&q=80",
      "https://images.unsplash.com/photo-1418065460487-3e41a6c84dc5?w=800&q=80",
      "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800&q=80",
      "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80",
      "https://images.unsplash.com/photo-1446329813274-7c9036bd9a1f?w=800&q=80",
      "https://images.unsplash.com/photo-1439853949127-fa647821eba0?w=800&q=80",
      "https://images.unsplash.com/photo-1505765050516-f72dcac9c60e?w=800&q=80",
      "https://images.unsplash.com/photo-1431794062232-2a99a5431c6c?w=800&q=80",
      "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800&q=80",
      "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&q=80",
      "https://images.unsplash.com/photo-1448375240586-882707db888b?w=800&q=80",
      "https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=800&q=80",
      "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80",
      "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80",
    ],
  },
  {
    key: "city",
    images: [
      "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=80",
      "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800&q=80",
      "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&q=80",
      "https://images.unsplash.com/photo-1444723121867-7a241cacace9?w=800&q=80",
      "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=800&q=80",
      "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=800&q=80",
      "https://images.unsplash.com/photo-1470004914212-05527e49370b?w=800&q=80",
      "https://images.unsplash.com/photo-1517935706615-2717063c2225?w=800&q=80",
      "https://images.unsplash.com/photo-1502899576159-f224dc2349fa?w=800&q=80",
      "https://images.unsplash.com/photo-1460306855393-0410f61241c7?w=800&q=80",
      "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?w=800&q=80",
      "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&q=80",
      "https://images.unsplash.com/photo-1513407030348-c983a97b98d8?w=800&q=80",
      "https://images.unsplash.com/photo-1534430480872-3498386e7856?w=800&q=80",
      "https://images.unsplash.com/photo-1543007630-9710e4a00a20?w=800&q=80",
      "https://images.unsplash.com/photo-1519114481-f3c3c5731de9?w=800&q=80",
      "https://images.unsplash.com/photo-1494522855154-9297ac14b55f?w=800&q=80",
      "https://images.unsplash.com/photo-1512850183-6d7990f42385?w=800&q=80",
      "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800&q=80",
      "https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=800&q=80",
    ],
  },
  {
    key: "sports",
    images: [
      "https://images.unsplash.com/photo-1461896836934-bd45ba48ab52?w=800&q=80",
      "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=800&q=80",
      "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=800&q=80",
      "https://images.unsplash.com/photo-1574629810360-7efad0449907?w=800&q=80",
      "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=800&q=80",
      "https://images.unsplash.com/photo-1541252260730-0412e8e2108e?w=800&q=80",
      "https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=800&q=80",
      "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50a?w=800&q=80",
      "https://images.unsplash.com/photo-1461897104016-0b3b00cc81ee?w=800&q=80",
      "https://images.unsplash.com/photo-1526676037777-05a232554f77?w=800&q=80",
      "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=800&q=80",
      "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=800&q=80",
      "https://images.unsplash.com/photo-1510682661854-0eb3ef2f5tried?w=800&q=80",
      "https://images.unsplash.com/photo-1599058917765-a780eda07a3e?w=800&q=80",
      "https://images.unsplash.com/photo-1544298621-a21e4e4cb0a3?w=800&q=80",
      "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800&q=80",
      "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=800&q=80",
      "https://images.unsplash.com/photo-1560272564-c83b66b1ad12?w=800&q=80",
      "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=800&q=80",
      "https://images.unsplash.com/photo-1471295253337-3ceaaedca402?w=800&q=80",
    ],
  },
  {
    key: "pets",
    images: [
      "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800&q=80",
      "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=800&q=80",
      "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=800&q=80",
      "https://images.unsplash.com/photo-1592194996308-7b43878e84a6?w=800&q=80",
      "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800&q=80",
      "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=800&q=80",
      "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?w=800&q=80",
      "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=800&q=80",
      "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=800&q=80",
      "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?w=800&q=80",
      "https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=800&q=80",
      "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=800&q=80",
      "https://images.unsplash.com/photo-1522276498395-f4f68f7f8571?w=800&q=80",
      "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=800&q=80",
      "https://images.unsplash.com/photo-1558929996-da64ba858215?w=800&q=80",
      "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=800&q=80",
      "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=800&q=80",
      "https://images.unsplash.com/photo-1517423440428-a5a00ad493e8?w=800&q=80",
      "https://images.unsplash.com/photo-1494947665470-20322015e3a8?w=800&q=80",
      "https://images.unsplash.com/photo-1507146426996-ef05306b995a?w=800&q=80",
    ],
  },
] as const;

interface CoverImagePickerProps {
  value: string;
  onSelect: (url: string | null) => void;
  label?: string;
}

export function CoverImagePicker({ value, onSelect, label }: CoverImagePickerProps) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);
  const [displayImages, setDisplayImages] = useState<{ key: string; images: string[] }[]>([]);

  // 每個分類各自維護一個 ShuffledPager，確保不重複
  const pagersRef = useRef<Map<string, ShuffledPager<string>>>(new Map());

  const getPagers = useCallback(() => {
    let pagers = pagersRef.current;
    if (pagers.size === 0) {
      for (const cat of PRESET_CATEGORIES) {
        pagers.set(cat.key, new ShuffledPager(cat.images));
      }
    }
    return pagers;
  }, []);

  const drawNextPage = useCallback(() => {
    const pagers = getPagers();
    setDisplayImages(
      PRESET_CATEGORIES.map((cat) => ({
        key: cat.key,
        images: pagers.get(cat.key)!.next(IMAGES_PER_PAGE),
      }))
    );
  }, [getPagers]);

  const handleShuffle = useCallback(() => {
    drawNextPage();
  }, [drawNextPage]);

  const handleConfirm = useCallback(() => {
    onSelect(selectedUrl);
    setVisible(false);
    setSelectedUrl(null);
  }, [selectedUrl, onSelect]);

  const handleRemove = useCallback(() => {
    onSelect(null);
    setVisible(false);
    setSelectedUrl(null);
  }, [onSelect]);

  const openPicker = useCallback(() => {
    setSelectedUrl(value || null);
    drawNextPage();
    setVisible(true);
  }, [value, drawNextPage]);

  const renderImageItem = useCallback(
    (url: string) => (
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
                <View className="flex-row items-center gap-3">
                  <Pressable onPress={handleShuffle} className="flex-row items-center gap-1">
                    <ArrowsClockwise size={20} color="hsl(240 3.8% 46.1%)" />
                    <Muted className="text-xs">{t("cover_shuffle")}</Muted>
                  </Pressable>
                  <Pressable onPress={() => setVisible(false)}>
                    <X size={24} color="hsl(240 3.8% 46.1%)" />
                  </Pressable>
                </View>
              </View>
            </View>

            {/* Content */}
            <ScrollView className="px-4" keyboardShouldPersistTaps="handled">
              <View>
                {displayImages.map((cat) => (
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

              {/* Unsplash attribution */}
              <Muted className="text-[10px] text-center mt-2 mb-4">
                Photos by Unsplash
              </Muted>
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
