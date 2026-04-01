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
  register: (data: { email: string; password: string; display_name: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  googleLogin: (accessToken: string) =>
    api.post("/auth/google", { access_token: accessToken }),
  getMe: () => api.get("/auth/me"),
  updateMe: (data: Record<string, string>) => api.patch("/auth/me", data),
  lookupByEmail: (email: string) =>
    api.get("/auth/lookup", { params: { email } }),
  changePassword: (old_password: string, new_password: string) =>
    api.patch("/auth/me/password", { old_password, new_password }),
};

// Groups
export const groupsAPI = {
  list: () => api.get("/groups"),
  get: (id: string) => api.get(`/groups/${id}`),
  create: (data: { name: string; description?: string; default_currency?: string }) =>
    api.post("/groups", data),
  update: (id: string, data: Record<string, string>) =>
    api.patch(`/groups/${id}`, data),
  delete: (id: string) => api.delete(`/groups/${id}`),
  addMember: (groupId: string, userId: string) =>
    api.post(`/groups/${groupId}/members`, { user_id: userId }),
  removeMember: (groupId: string, userId: string) =>
    api.delete(`/groups/${groupId}/members/${userId}`),
};

export interface ExpenseSplitInput {
  user_id: string;
  amount?: number;
  shares?: number;
}

export interface ExpenseCreatePayload {
  description: string;
  total_amount: number;
  currency?: string;
  paid_by: string;
  split_method?: "equal" | "exact" | "ratio" | "shares";
  splits?: ExpenseSplitInput[];
  note?: string;
}

export interface SettlementCreatePayload {
  to_user: string;
  amount: number;
  currency: string;
  note?: string;
}

// Expenses
export const expensesAPI = {
  list: (groupId: string) => api.get(`/groups/${groupId}/expenses`),
  get: (groupId: string, id: string) =>
    api.get(`/groups/${groupId}/expenses/${id}`),
  create: (groupId: string, data: ExpenseCreatePayload) =>
    api.post(`/groups/${groupId}/expenses`, data),
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
};

// Activities
export const activitiesAPI = {
  list: (skip = 0, limit = 20) =>
    api.get("/activities", { params: { skip, limit } }),
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
