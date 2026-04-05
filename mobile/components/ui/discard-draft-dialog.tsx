import { Modal, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Text, H3 } from "~/components/ui/text";
import { Button } from "~/components/ui/button";
import { useThemeClassName } from "~/lib/theme";

interface DiscardDraftDialogProps {
  visible: boolean;
  onDiscard: () => void;
  onCancel: () => void;
}

export function DiscardDraftDialog({ visible, onDiscard, onCancel }: DiscardDraftDialogProps) {
  const { t } = useTranslation();
  const themeClass = useThemeClassName();

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <View className={`flex-1 ${themeClass}`}>
        <View className="flex-1 justify-center items-center bg-black/50 px-6">
          <View className="bg-background rounded-xl p-6 w-full max-w-sm gap-4">
            <H3>{t("discard_draft_title")}</H3>
            <Text className="text-muted-foreground">{t("discard_draft_message")}</Text>
            <View className="flex-row gap-3 justify-end">
              <Button variant="outline" onPress={onCancel}>
                {t("continue_editing")}
              </Button>
              <Button variant="destructive" onPress={onDiscard}>
                {t("discard")}
              </Button>
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}
