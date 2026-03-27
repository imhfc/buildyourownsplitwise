import axios from "axios";
import { useAuthStore } from "../stores/auth";

// Change this to your backend URL
const API_BASE_URL = __DEV__
  ? "http://localhost:8001/api/v1"
  : "https://your-production-url.com/api/v1";

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

// Auth
export const authAPI = {
  register: (data: { email: string; password: string; display_name: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  getMe: () => api.get("/auth/me"),
  updateMe: (data: Record<string, string>) => api.patch("/auth/me", data),
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

// Expenses
export const expensesAPI = {
  list: (groupId: string) => api.get(`/groups/${groupId}/expenses`),
  get: (groupId: string, id: string) =>
    api.get(`/groups/${groupId}/expenses/${id}`),
  create: (groupId: string, data: any) =>
    api.post(`/groups/${groupId}/expenses`, data),
  delete: (groupId: string, id: string) =>
    api.delete(`/groups/${groupId}/expenses/${id}`),
};

// Settlements
export const settlementsAPI = {
  suggestions: (groupId: string) =>
    api.get(`/groups/${groupId}/settlements/suggestions`),
  list: (groupId: string) => api.get(`/groups/${groupId}/settlements`),
  create: (groupId: string, data: any) =>
    api.post(`/groups/${groupId}/settlements`, data),
};

export default api;
