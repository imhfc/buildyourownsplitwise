import { View } from "react-native";
import { useTranslation } from "react-i18next";
import { UserPlus } from "lucide-react-native";
import { EmptyState } from "~/components/ui/empty-state";

export default function FriendsScreen() {
  const { t } = useTranslation();
  return (
    <View className="flex-1 bg-background">
      <EmptyState
        icon={UserPlus}
        title={t("friends_coming_soon")}
        description={t("friends_coming_soon_desc")}
      />
    </View>
  );
}
