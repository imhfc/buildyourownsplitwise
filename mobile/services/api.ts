import axios from "axios";
import { useAuthStore } from "../stores/auth";

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (__DEV__ ? "http://localhost:8001/api/v1" : "/api/v1");

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh token on 401/403
let refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    // Only retry once, skip auth endpoints
    if (
      (status === 401 || status === 403) &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/")
    ) {
      originalRequest._retry = true;
      const { refreshToken, logout, setTokens } = useAuthStore.getState();

      if (!refreshToken) {
        logout();
        return Promise.reject(error);
      }

      try {
        // Deduplicate concurrent refresh calls
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
            .then((res) => {
              setTokens(res.data.access_token, res.data.refresh_token);
              return res.data.access_token as string;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }

        const newToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch {
        logout();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  googleLogin: (accessToken: string) =>
    api.post("/auth/google", { access_token: accessToken }),
  getMe: () => api.get("/auth/me"),
  updateMe: (data: Record<string, string>) => api.patch("/auth/me", data),
  lookupByEmail: (email: string) =>
    api.get("/auth/lookup", { params: { email } }),
};

// Groups
export const groupsAPI = {
  list: () => api.get("/groups"),
  get: (id: string) => api.get(`/groups/${id}`),
  create: (data: { name: string; description?: string; default_currency?: string }) =>
    api.post("/groups", data),
  update: (id: string, data: Record<string, unknown>) =>
    api.patch(`/groups/${id}`, data),
  delete: (id: string) => api.delete(`/groups/${id}`),
  addMember: (groupId: string, userId: string) =>
    api.post(`/groups/${groupId}/members`, { user_id: userId }),
  removeMember: (groupId: string, userId: string) =>
    api.delete(`/groups/${groupId}/members/${userId}`),
  reorder: (groupIds: string[]) =>
    api.put("/groups/reorder", { group_ids: groupIds }),
  createInvite: (groupId: string) =>
    api.post(`/groups/${groupId}/invite`),
  revokeInvite: (groupId: string) =>
    api.delete(`/groups/${groupId}/invite`),
  regenerateInvite: (groupId: string) =>
    api.post(`/groups/${groupId}/invite/regenerate`),
  sendEmailInvitation: (groupId: string, email: string) =>
    api.post(`/groups/${groupId}/email-invitations`, { email }),
  listEmailInvitations: (groupId: string) =>
    api.get(`/groups/${groupId}/email-invitations`),
};

// Invites (receiver-side)
export const inviteAPI = {
  getInfo: (token: string) => api.get(`/invite/${token}`),
  accept: (token: string) => api.post(`/invite/${token}/accept`),
  getMyPendingInvitations: () => api.get("/invite/email/pending"),
  respondToInvitation: (id: string, action: "accept" | "decline") =>
    api.post(`/invite/email/${id}/respond`, { action }),
};

export interface ExpenseSplitInput {
  user_id: string;
  amount?: number;
  shares?: number;
}

export interface ExpensePayerInput {
  user_id: string;
  amount: number;
}

export interface ExpenseCreatePayload {
  description: string;
  total_amount: number;
  currency?: string;
  paid_by: string;
  payers?: ExpensePayerInput[];
  split_method?: "equal" | "exact" | "ratio" | "shares";
  splits?: ExpenseSplitInput[];
  note?: string;
}

export interface ExpenseUpdatePayload {
  description?: string;
  total_amount?: number;
  currency?: string;
  paid_by?: string;
  payers?: ExpensePayerInput[];
  split_method?: string;
  splits?: ExpenseSplitInput[];
  note?: string;
}

export interface SettlementCreatePayload {
  to_user: string;
  amount: number;
  currency: string;
  note?: string;
  original_currency?: string;
  original_amount?: number;
  locked_rate?: number;
}

// Expenses
export const expensesAPI = {
  list: (groupId: string) => api.get(`/groups/${groupId}/expenses`),
  get: (groupId: string, id: string) =>
    api.get(`/groups/${groupId}/expenses/${id}`),
  create: (groupId: string, data: ExpenseCreatePayload) =>
    api.post(`/groups/${groupId}/expenses`, data),
  update: (groupId: string, id: string, data: ExpenseUpdatePayload) =>
    api.patch(`/groups/${groupId}/expenses/${id}`, data),
  delete: (groupId: string, id: string) =>
    api.delete(`/groups/${groupId}/expenses/${id}`),
};

// Settlements
export const settlementsAPI = {
  suggestions: (groupId: string) =>
    api.get(`/groups/${groupId}/settlements/suggestions`),
  list: (groupId: string) => api.get(`/groups/${groupId}/settlements`),
  create: (groupId: string, data: SettlementCreatePayload) =>
    api.post(`/groups/${groupId}/settlements`, data),
  confirm: (groupId: string, settlementId: string) =>
    api.patch(`/groups/${groupId}/settlements/${settlementId}/confirm`),
  pending: () => api.get("/settlements/pending"),
  pairwiseDetails: (groupId: string) =>
    api.get(`/groups/${groupId}/settlements/details`),
  sendReminder: (groupId: string, data: { to_user: string; amount: number; currency: string }) =>
    api.post(`/groups/${groupId}/settlements/reminders`, data),
};

// Balances
export const balancesAPI = {
  overall: () => api.get("/balances"),
  group: (groupId: string) => api.get(`/balances/groups/${groupId}`),
};

// Activities
export const activitiesAPI = {
  list: (skip = 0, limit = 20) =>
    api.get("/activities", { params: { skip, limit } }),
  unreadCount: () => api.get<{ count: number }>("/activities/unread-count"),
  markRead: () => api.post<{ count: number }>("/activities/mark-read"),
};

// Exchange Rates
export const exchangeRatesAPI = {
  currencies: () => api.get("/exchange-rates/currencies"),
  list: () => api.get("/exchange-rates"),
  convert: (data: { from_currency: string; to_currency: string; amount: number }) =>
    api.post("/exchange-rates/convert", data),
};

// Friends
export const friendsAPI = {
  list: () => api.get("/friends"),
  search: (q: string) => api.get("/friends/search", { params: { q } }),
  getRequests: () => api.get("/friends/requests"),
  sendRequest: (email: string) =>
    api.post("/friends/requests", { friend_email: email }),
  handleRequest: (id: string, action: "accept" | "reject") =>
    api.patch(`/friends/requests/${id}`, { action }),
  removeFriend: (friendId: string) =>
    api.delete(`/friends/${friendId}`),
};

export default api;
