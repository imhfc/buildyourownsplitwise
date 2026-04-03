/**
 * Push Notification 工具模組
 *
 * 使用前需先安裝：npx expo install expo-notifications expo-device expo-constants
 * 然後在 app/_layout.tsx 中呼叫 registerForPushNotifications()
 */
import { Platform } from "react-native";
import { authAPI } from "../services/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
let Notifications: any = null;
let Device: any = null;
let Constants: any = null;

// 延遲載入（避免未安裝時 crash）
async function loadModules(): Promise<boolean> {
  try {
    Notifications = require("expo-notifications");
    Device = require("expo-device");
    Constants = require("expo-constants");
    return true;
  } catch {
    console.warn("expo-notifications not installed. Push notifications disabled.");
    return false;
  }
}

export async function registerForPushNotifications(): Promise<string | null> {
  const loaded = await loadModules();
  if (!loaded || !Notifications || !Device || !Constants) return null;

  // 只在實體裝置上註冊
  if (!Device.isDevice) {
    console.warn("Push notifications only work on physical devices");
    return null;
  }

  // 請求權限
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    return null;
  }

  // 取得 Expo Push Token
  try {
    const projectId = Constants?.expoConfig?.extra?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined,
    );
    const token = tokenData.data;

    // 上傳 token 到後端
    try {
      await authAPI.updateMe({ push_token: token });
    } catch (e) {
      console.error("Failed to upload push token:", e);
    }

    // Android 需要設定通知頻道
    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("default", {
        name: "Default",
        importance: 4, // AndroidImportance.MAX
        vibrationPattern: [0, 250, 250, 250],
      });
    }

    return token;
  } catch (e) {
    console.error("Failed to get push token:", e);
    return null;
  }
}

export function setupNotificationHandlers() {
  if (!Notifications) return;

  // 前景通知顯示設定
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: true,
    }),
  });
}

/**
 * 監聽前景收到的推播通知，觸發 callback 刷新資料。
 * 回傳 cleanup 函式供 useEffect 使用。
 */
export function addNotificationReceivedCallback(callback: () => void): () => void {
  if (!Notifications) return () => {};

  const subscription = Notifications.addNotificationReceivedListener(() => {
    callback();
  });

  return () => subscription.remove();
}
