/**
 * Personal AI OS - API Service
 * API 请求服务
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 创建 axios 实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证令牌
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理认证错误
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 清除本地存储的令牌
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // 跳转到登录页面
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ========== Auth API ==========
export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  
  refreshToken: (refreshToken: string) =>
    api.post(`/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`),
  
  getMe: () => api.get('/auth/me'),
  
  logout: () => api.post('/auth/logout'),
};

// ========== User API ==========
export const userApi = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data: any) => api.put('/users/profile', data),
};

// ========== Document API ==========
export const documentApi = {
  upload: (formData: FormData) =>
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  list: (params?: { page?: number; limit?: number }) =>
    api.get('/documents', { params }),
  
  get: (id: string) => api.get(`/documents/${id}`),
  
  delete: (id: string) => api.delete(`/documents/${id}`),
};

// ========== Knowledge API ==========
export const knowledgeApi = {
  search: (query: string, limit?: number) =>
    api.post('/knowledge/search', { query, limit }),
  
  create: (data: { name: string; category?: string }) =>
    api.post('/knowledge/create', data),
};

// ========== AI API ==========
export const aiApi = {
  chat: (data: {
    message: string;
    conversation_id?: string;
    memory_enabled?: boolean;
  }) => api.post('/ai/chat', data),
  
  summary: (data: { content: string; type?: string }) =>
    api.post('/ai/summary', data),
  
  listConversations: (params?: { limit?: number }) =>
    api.get('/ai/conversations', { params }),
  
  getConversationMessages: (conversationId: string) =>
    api.get(`/ai/conversations/${conversationId}`),

  deleteConversation: (conversationId: string) =>
    api.delete(`/ai/conversations/${conversationId}`),
};

// ========== Memory API ==========
export const memoryApi = {
  create: (data: {
    content: string;
    memory_type: string;
    importance?: number;
    source?: string;
  }) => api.post('/memory', data),
  
  list: (params?: { page?: number; limit?: number; memory_type?: string }) =>
    api.get('/memory', { params }),
  
  get: (id: string) => api.get(`/memory/${id}`),
  
  update: (id: string, data: any) => api.put(`/memory/${id}`, data),
  
  delete: (id: string) => api.delete(`/memory/${id}`),
  
  search: (params: { query?: string; memory_type?: string; limit?: number }) =>
    api.post('/memory/search', params),
  
  stats: () => api.get('/memory/stats/summary'),
};

// ========== Settings API ==========
export const settingsApi = {
  get: () => api.get('/settings'),
  
  update: (data: any) => api.put('/settings', data),
  
  getModels: (apiKey: string) => api.get('/settings/models', { params: { api_key: apiKey } }),
  
  testConnection: () => api.post('/settings/test-connection'),
};
export const cognitiveApi = {
  // 观点管理
  createBelief: (data: {
    topic: string;
    content: string;
    confidence?: number;
    supporting_evidence?: string[];
    opposing_evidence?: string[];
  }) => api.post('/cognitive/beliefs', data),
  
  listBeliefs: (params?: { page?: number; limit?: number; topic?: string }) =>
    api.get('/cognitive/beliefs', { params }),
  
  getBelief: (id: string) => api.get(`/cognitive/beliefs/${id}`),
  
  updateBelief: (id: string, data: any) => api.put(`/cognitive/beliefs/${id}`, data),
  
  deleteBelief: (id: string) => api.delete(`/cognitive/beliefs/${id}`),
  
  getBeliefHistory: (id: string) => api.get(`/cognitive/beliefs/${id}/history`),
};

// ========== Decision API ==========
export const decisionApi = {
  create: (data: {
    problem: string;
    background?: string;
    options?: string[];
    choice?: string;
    reasoning?: string;
    risk?: string;
    category?: string;
  }) => api.post('/decision', data),
  
  list: (params?: { page?: number; limit?: number; category?: string }) =>
    api.get('/decision', { params }),
  
  get: (id: string) => api.get(`/decision/${id}`),
  
  update: (id: string, data: any) => api.put(`/decision/${id}`, data),
  
  delete: (id: string) => api.delete(`/decision/${id}`),
  
  stats: () => api.get('/decision/stats/summary'),
};

// ========== Usage API ==========
export const usageApi = {
  getStats: () => api.get('/usage/stats'),
  getLimits: () => api.get('/usage/limits'),
};

// ========== Agent API ==========
export const agentApi = {
  list: () => api.get('/agent/list'),
  run: (data: { agent_type: string; input: string; title?: string; context?: any }) =>
    api.post('/agent/run', data),
  listTasks: (params?: { page?: number; limit?: number; agent_type?: string }) =>
    api.get('/agent/tasks', { params }),
  getTask: (taskId: string) => api.get(`/agent/tasks/${taskId}`),
};

// ========== Multimodal API ==========
export const multimodalApi = {
  analyzeImage: (data: { image_base64: string; question: string }) =>
    api.post('/multimodal/analyze-image', data),
  
  uploadImage: (formData: FormData) =>
    api.post('/multimodal/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
};

// ========== Voice API ==========
export const voiceApi = {
  transcribe: (formData: FormData) =>
    api.post('/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  listModels: () => api.get('/voice/models'),
};

// ========== Graph API ==========
export const graphApi = {
  getData: () => api.get('/graph'),
};
