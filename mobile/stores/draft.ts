import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

const storage = createJSONStorage(() =>
  Platform.OS === "web" ? localStorage : AsyncStorage
);

const DRAFT_TTL_MS = 10_000; // 10 seconds

interface DraftEntry {
  data: Record<string, unknown>;
  savedAt: number;
}

interface DraftState {
  drafts: Record<string, DraftEntry>;
  saveDraft: (key: string, data: Record<string, unknown>) => void;
  getDraft: (key: string) => Record<string, unknown> | null;
  clearDraft: (key: string) => void;
  clearExpired: () => void;
}

export const useDraftStore = create<DraftState>()(
  persist(
    (set, get) => ({
      drafts: {},

      saveDraft: (key, data) =>
        set((state) => ({
          drafts: {
            ...state.drafts,
            [key]: { data, savedAt: Date.now() },
          },
        })),

      getDraft: (key) => {
        const entry = get().drafts[key];
        if (!entry) return null;
        if (Date.now() - entry.savedAt > DRAFT_TTL_MS) {
          get().clearDraft(key);
          return null;
        }
        return entry.data;
      },

      clearDraft: (key) =>
        set((state) => {
          const { [key]: _, ...rest } = state.drafts;
          return { drafts: rest };
        }),

      clearExpired: () =>
        set((state) => {
          const now = Date.now();
          const valid = Object.fromEntries(
            Object.entries(state.drafts).filter(
              ([, v]) => now - v.savedAt <= DRAFT_TTL_MS
            )
          );
          return { drafts: valid };
        }),
    }),
    {
      name: "draft-storage",
      storage,
    }
  )
);
