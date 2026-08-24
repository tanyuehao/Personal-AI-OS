/**
 * Personal AI OS - Auth Store
 * 认证状态管理
 */
import { create } from 'zustand';
import { authApi } from '@/services/api';

interface User {
  user_id: string;
  username: string;
  email: string;
  name?: string;
  avatar?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  
  login: async (email: string, password: string) => {
    try {
      const response = await authApi.login({ email, password });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // 获取用户信息
      const userResponse = await authApi.getMe();
      set({
        user: userResponse.data,
        isAuthenticated: true,
      });
    } catch (error) {
      throw error;
    }
  },
  
  register: async (username: string, email: string, password: string) => {
    try {
      await authApi.register({ username, email, password });
      // 注册成功后自动登录
      await useAuthStore.getState().login(email, password);
    } catch (error) {
      throw error;
    }
  },
  
  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    try {
      await authApi.logout(refreshToken || undefined);
    } catch (e) {
      // 忽略登出错误
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({
      user: null,
      isAuthenticated: false,
    });
  },
  
  checkAuth: async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        set({ isLoading: false });
        return;
      }
      
      const response = await authApi.getMe();
      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
}));
