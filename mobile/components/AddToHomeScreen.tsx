import { useState } from "react";
import { View, Pressable, Modal, Linking } from "react-native";
import { useTranslation } from "react-i18next";
import { DeviceMobileCamera, Export, DotsThree, X, Compass } from "phosphor-react-native";
import { useInstallPrompt } from "~/lib/use-install-prompt";
import { useThemeClassName } from "~/lib/theme";
import { Text } from "~/components/ui/text";
import { Button } from "~/components/ui/button";

function StepRow({
  step,
  children,
}: {
  step: number;
  children: React.ReactNode;
}) {
  return (
    <View className="flex-row items-center gap-3">
      <View className="h-9 w-9 items-center justify-center rounded-lg bg-muted">
        <Text className="text-sm font-semibold text-foreground">{step}</Text>
      </View>
      <View className="flex-1">{children}</View>
    </View>
  );
}

/**
 * "Add to Home Screen" banner.
 * Renders nothing when not on mobile web or already installed as PWA.
 */
export function AddToHomeScreen() {
  const { t } = useTranslation();
  const { canInstall, iosBrowser, promptInstall } = useInstallPrompt();
  const [showGuide, setShowGuide] = useState(false);
  const themeClass = useThemeClassName();

  if (!canInstall) return null;

  const handlePress = () => {
    if (iosBrowser) {
      setShowGuide(true);
    } else {
      promptInstall();
    }
  };

  const handleOpenInSafari = () => {
    Linking.openURL(window.location.href);
  };

  const iconColor = "hsl(var(--primary-foreground))";

  return (
    <>
      <Button
        variant="default"
        onPress={handlePress}
        className="flex-row items-center justify-center gap-2"
      >
        <DeviceMobileCamera size={18} color={iconColor} weight="regular" />
        <Text className="text-sm font-medium text-primary-foreground">
          {t("add_to_home_screen")}
        </Text>
      </Button>

      {/* iOS instruction modal */}
      <Modal
        visible={showGuide}
        transparent
        animationType="slide"
        onRequestClose={() => setShowGuide(false)}
      >
        <View className={`flex-1 ${themeClass}`}>
          <View className="flex-1 justify-end bg-black/50">
            <View className="bg-background border-t border-border rounded-t-xl px-5 pb-10 pt-4">
              <View className="items-center mb-4">
                <View className="h-1 w-8 rounded-full bg-muted-foreground/20" />
              </View>
              <View className="flex-row items-center justify-between mb-5">
                <Text className="text-base font-semibold">
                  {t("add_to_home_screen")}
                </Text>
                <Pressable
                  onPress={() => setShowGuide(false)}
                  hitSlop={8}
                >
                  <X size={20} color="#737373" />
                </Pressable>
              </View>

              {iosBrowser === "inapp" ? (
                /* ── In-app browser (LINE / Facebook): must open in real browser ── */
                <View className="gap-4">
                  <Text className="text-sm text-muted-foreground">
                    {t("ios_need_safari")}
                  </Text>
                  <StepRow step={1}>
                    <View className="flex-row items-center gap-2">
                      <Text className="text-sm text-foreground">
                        {t("ios_open_safari")}
                      </Text>
                      <Compass size={18} color="#737373" weight="regular" />
                    </View>
                  </StepRow>
                  <StepRow step={2}>
                    <View className="flex-row items-center gap-2">
                      <Text className="text-sm text-foreground">
                        {t("ios_step_1")}
                      </Text>
                      <Export size={18} color="#737373" weight="regular" />
                    </View>
                  </StepRow>
                  <StepRow step={3}>
                    <Text className="text-sm text-foreground">
                      {t("ios_step_2")}
                    </Text>
                  </StepRow>
                  <Button onPress={handleOpenInSafari} className="mt-4">
                    {t("open_in_safari")}
                  </Button>
                </View>
              ) : iosBrowser === "chrome" ? (
                /* ── iOS Chrome: ⋯ menu > Add to Home Screen ── */
                <View className="gap-4">
                  <StepRow step={1}>
                    <View className="flex-row items-center gap-2">
                      <Text className="text-sm text-foreground">
                        {t("ios_chrome_step_1")}
                      </Text>
                      <DotsThree size={18} color="#737373" weight="bold" />
                    </View>
                  </StepRow>
                  <StepRow step={2}>
                    <Text className="text-sm text-foreground">
                      {t("ios_step_2")}
                    </Text>
                  </StepRow>
                  <StepRow step={3}>
                    <Text className="text-sm text-foreground">
                      {t("ios_step_3")}
                    </Text>
                  </StepRow>
                </View>
              ) : (
                /* ── iOS Safari (and others like Firefox/Edge): Share > Add ── */
                <View className="gap-4">
                  <StepRow step={1}>
                    <View className="flex-row items-center gap-2">
                      <Text className="text-sm text-foreground">
                        {t("ios_step_1")}
                      </Text>
                      <Export size={18} color="#737373" weight="regular" />
                    </View>
                  </StepRow>
                  <StepRow step={2}>
                    <Text className="text-sm text-foreground">
                      {t("ios_step_2")}
                    </Text>
                  </StepRow>
                  <StepRow step={3}>
                    <Text className="text-sm text-foreground">
                      {t("ios_step_3")}
                    </Text>
                  </StepRow>
                </View>
              )}

              <Button
                variant="outline"
                onPress={() => setShowGuide(false)}
                className="mt-6"
              >
                {t("confirm")}
              </Button>
            </View>
          </View>
        </View>
      </Modal>
    </>
  );
}
