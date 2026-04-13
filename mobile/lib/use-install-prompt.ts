import { useState, useEffect, useCallback } from "react";
import { Platform } from "react-native";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

/**
 * iOS browser detection result.
 * - "safari"  → Share button > Add to Home Screen
 * - "chrome"  → ⋯ menu > Add to Home Screen
 * - "inapp"   → in-app browser (LINE/FB), must open in Safari/Chrome
 * - null      → not iOS
 */
type IOSBrowser = "safari" | "chrome" | "inapp" | null;

/**
 * PWA "Add to Home Screen" hook.
 */
export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [iosBrowser, setIOSBrowser] = useState<IOSBrowser>(null);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (Platform.OS !== "web") return;

    // Already running as installed PWA?
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as any).standalone === true;
    setIsInstalled(standalone);

    const ua = navigator.userAgent;
    const mobile = /iPhone|iPad|iPod|Android/i.test(ua);
    setIsMobile(mobile);

    // Detect iOS browser variant
    const ios = /iPhone|iPad|iPod/i.test(ua);
    if (ios) {
      if (/FBAN|FBAV|Line\//i.test(ua)) {
        setIOSBrowser("inapp");
      } else if (/CriOS/i.test(ua)) {
        setIOSBrowser("chrome");
      } else {
        // Safari, Firefox(FxiOS), Edge(EdgiOS) etc. all support Share > Add to Home Screen
        setIOSBrowser("safari");
      }
    }

    // Listen for the browser's install prompt (Chrome / Edge on Android)
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);

    const onInstalled = () => setIsInstalled(true);
    window.addEventListener("appinstalled", onInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", handler);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const promptInstall = useCallback(async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") {
      setIsInstalled(true);
    }
    setDeferredPrompt(null);
  }, [deferredPrompt]);

  const canInstall =
    Platform.OS === "web" &&
    isMobile &&
    !isInstalled &&
    (deferredPrompt !== null || iosBrowser !== null);

  return { canInstall, iosBrowser, promptInstall };
}
