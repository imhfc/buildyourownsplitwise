import { create } from "zustand";
import { settlementsAPI } from "../services/api";

interface PendingSettlementsState {
  count: number;
  fetchCount: () => Promise<void>;
  decrement: () => void;
  clearCount: () => void;
}

export const usePendingSettlementsStore = create<PendingSettlementsState>()(
  (set) => ({
    count: 0,

    fetchCount: async () => {
      try {
        const res = await settlementsAPI.pending();
        set({ count: res.data.length });
      } catch {
        // silent fail
      }
    },

    decrement: () => set((s) => ({ count: Math.max(0, s.count - 1) })),

    clearCount: () => set({ count: 0 }),
  })
);
