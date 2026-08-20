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
  candidates: (params?: { limit?: number }) =>
    api.get('/memory/candidates', { params }),
  confirm: (id: string) => api.post(`/memory/${id}/confirm`),
  reject: (id: string) => api.post(`/memory/${id}/reject`),
  confirmAll: () => api.post('/memory/confirm-all'),
  rejectAll: () => api.post('/memory/reject-all'),
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
  getTimeline: () => api.get('/cognitive/beliefs/timeline'),
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

// ========== Export API ==========
export const exportApi = {
  exportAll: () => `${API_BASE_URL}/api/v1/export/all`,
  getStats: () => api.get('/export/stats'),
};

// ========== Cognitive Engine API ==========
export const cognitiveEngineApi = {
  extractBeliefs: (messages: Array<{role: string; content: string}>) =>
    api.post('/cognitive/beliefs/extract', { messages }),
  checkConflict: (content: string, topic?: string) =>
    api.post('/cognitive/beliefs/check-conflict', { content, topic }),
  linkDecision: (decision_id: string) =>
    api.post('/cognitive/decisions/link', { decision_id }),
  getMemoryScore: (params: { importance?: number; confidence?: number; frequency?: number; user_confirmed?: boolean }) =>
    api.get('/cognitive/memory-score', { params }),
};

// ========== Reflection API ==========
export const reflectionApi = {
  findDuplicates: () => api.get('/reflection/duplicates'),
  detectConflicts: () => api.get('/reflection/conflicts'),
  getWeeklySummary: (days?: number) => api.get('/reflection/weekly-summary', { params: { days } }),
  consolidate: () => api.post('/reflection/consolidate'),
};

// ========== Decision Style API ==========
export const decisionStyleApi = {
  getStyle: () => api.get('/cognitive/decision-style'),
  analyzeStyle: () => api.post('/cognitive/decision-style/analyze'),
  getPatterns: () => api.get('/cognitive/decision-style/patterns'),
  getRecommendations: (decision_context: string) =>
    api.post('/cognitive/decision-style/recommendations', { decision_context }),
  getStyleTypes: () => api.get('/cognitive/decision-style/types'),
};

// ========== Knowledge Graph Modeling API ==========
export const knowledgeGraphApi = {
  getGraph: (params?: { entity_type?: string; limit?: number }) =>
    api.get('/knowledge-graph', { params }),
  buildGraph: (limit?: number) =>
    api.post('/knowledge-graph/build', { limit: limit || 50 }),
  getEntityConnections: (entity_name: string) =>
    api.get(`/knowledge-graph/entity/${encodeURIComponent(entity_name)}`),
  getTypes: () => api.get('/knowledge-graph/types'),
};

// ========== Memory Network API ==========
export const memoryNetworkApi = {
  getStats: () => api.get('/memory-network/stats'),
  reinforce: (memory_id: string, reinforcement?: number) =>
    api.post(`/memory-network/reinforce/${memory_id}`, null, { params: { reinforcement } }),
  batchReinforce: (memory_ids: string[], reinforcement?: number) =>
    api.post('/memory-network/batch-reinforce', memory_ids, { params: { reinforcement } }),
  createAssociation: (data: { source_memory_id: string; target_memory_id: string; association_type?: string; strength?: number; context?: string }) =>
    api.post('/memory-network/association', data),
  recall: (memory_id: string, limit?: number) =>
    api.get(`/memory-network/recall/${memory_id}`, { params: { limit } }),
  cluster: () => api.post('/memory-network/cluster'),
  getStrengths: () => api.get('/memory-network/strengths'),
  getTypes: () => api.get('/memory-network/types'),
};

// ========== Communication Style API ==========
export const communicationStyleApi = {
  getStyle: () => api.get('/cognitive/communication-style'),
  analyzeStyle: () => api.post('/cognitive/communication-style/analyze'),
  getHabits: () => api.get('/cognitive/communication-style/habits'),
  getPatterns: () => api.get('/cognitive/communication-style/patterns'),
  getTypes: () => api.get('/cognitive/communication-style/types'),
};

// ========== Proactive Intelligence API ==========
export const proactiveApi = {
  getContext: () => api.get('/proactive/context'),
  generateInsights: () => api.post('/proactive/insights/generate'),
  getInsights: (unreadOnly?: boolean) =>
    api.get('/proactive/insights', { params: { unread_only: unreadOnly } }),
  markInsightRead: (id: string) => api.post(`/proactive/insights/${id}/read`),
  dismissInsight: (id: string) => api.post(`/proactive/insights/${id}/dismiss`),
  predictTrends: () => api.post('/proactive/trends/predict'),
  getTrends: () => api.get('/proactive/trends'),
  getTypes: () => api.get('/proactive/types'),
};

// ========== Learning API ==========
export const learningApi = {
  // 修正
  recordCorrection: (data: { conversation_id?: string; original_response: string; correction: string; correction_type?: string }) =>
    api.post('/learning/corrections', data),
  getCorrections: (limit?: number) =>
    api.get('/learning/corrections', { params: { limit } }),

  // 偏好
  learnPreference: (data: { category: string; key: string; value: string; confidence?: number }) =>
    api.post('/learning/preferences', data),
  getPreferences: (category?: string) =>
    api.get('/learning/preferences', { params: { category } }),

  // 反馈
  recordFeedback: (data: { conversation_id?: string; message_id?: string; rating: number; comment?: string; feedback_type?: string }) =>
    api.post('/learning/feedback', data),
  getFeedbackStats: () => api.get('/learning/feedback/stats'),

  // 学习事件和统计
  getEvents: (limit?: number) =>
    api.get('/learning/events', { params: { limit } }),
  getStats: () => api.get('/learning/stats'),
  updateModel: () => api.post('/learning/update-model'),
};

// ========== Reasoning API ==========
export const reasoningApi = {
  analyze: (query: string, reasoning_type?: string) =>
    api.post('/reasoning/analyze', { query, reasoning_type }),
  multiStep: (query: string) =>
    api.post('/reasoning/multi-step', { query }),
  analogy: (situation: string) =>
    api.post('/reasoning/analogy', { situation }),
  getHistory: (limit?: number) =>
    api.get('/reasoning/history', { params: { limit } }),
  getAnalogies: (limit?: number) =>
    api.get('/reasoning/analogies', { params: { limit } }),
  generateSuggestions: () =>
    api.post('/reasoning/suggestions/generate'),
  getSuggestions: (limit?: number) =>
    api.get('/reasoning/suggestions', { params: { limit } }),
  getTypes: () => api.get('/reasoning/types'),
};

// ========== Prediction API ==========
export const predictionApi = {
  getPatterns: () => api.get('/prediction/patterns'),
  predict: () => api.post('/prediction/predict'),
  getPredictions: (limit?: number) =>
    api.get('/prediction/predictions', { params: { limit } }),
  prepareInfo: (prediction_id: string) =>
    api.post(`/prediction/prepare/${prediction_id}`),
  getPreparedInfos: (limit?: number) =>
    api.get('/prediction/prepared', { params: { limit } }),
  getTypes: () => api.get('/prediction/types'),
};

// ========== Context Awareness API ==========
export const contextApi = {
  startSession: (data: { session_type?: string; title?: string; description?: string }) =>
    api.post('/context/session/start', data),
  endSession: (sessionId: string) =>
    api.post(`/context/session/${sessionId}/end`),
  getSessions: (limit?: number) =>
    api.get('/context/sessions', { params: { limit } }),
  logActivity: (data: { activity_type: string; action: string; details?: string; page?: string; tool?: string }) =>
    api.post('/context/activity', data),
  getActivities: (hours?: number, limit?: number) =>
    api.get('/context/activities', { params: { hours, limit } }),
  getActivityStats: () => api.get('/context/activities/stats'),
  detectFocus: () => api.post('/context/focus/detect'),
  getFocus: () => api.get('/context/focus'),
  getCurrentContext: () => api.get('/context/current'),
  getTypes: () => api.get('/context/types'),
};

// ========== Autonomous Action API ==========
export const autonomousApi = {
  plan: (goal: string, context?: string) =>
    api.post('/autonomous/plan', { goal, context }),
  execute: (planId: string) =>
    api.post(`/autonomous/execute/${planId}`),
  approve: (planId: string) =>
    api.post(`/autonomous/approve/${planId}`),
  reject: (planId: string) =>
    api.post(`/autonomous/reject/${planId}`),
  getPlans: (status?: string, limit?: number) =>
    api.get('/autonomous/plans', { params: { status, limit } }),
  getPending: () => api.get('/autonomous/pending'),
  getStats: () => api.get('/autonomous/stats'),
  createRule: (data: { rule_name: string; description: string; rule_type: string; condition: string; action?: string }) =>
    api.post('/autonomous/rules', data),
  getRules: () => api.get('/autonomous/rules'),
  getTypes: () => api.get('/autonomous/types'),
};
