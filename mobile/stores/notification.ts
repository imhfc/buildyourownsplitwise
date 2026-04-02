import { create } from "zustand";
import { activitiesAPI } from "../services/api";

interface NotificationState {
  unreadCount: number;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: () => Promise<void>;
  clearCount: () => void;
}

export const useNotificationStore = create<NotificationState>()((set) => ({
  unreadCount: 0,

  fetchUnreadCount: async () => {
    try {
      const res = await activitiesAPI.unreadCount();
      set({ unreadCount: res.data.count });
    } catch {
      // 未登入或網路錯誤時忽略
    }
  },

  markAsRead: async () => {
    try {
      await activitiesAPI.markRead();
      set({ unreadCount: 0 });
    } catch {
      // silent fail
    }
  },

  clearCount: () => set({ unreadCount: 0 }),
}));
