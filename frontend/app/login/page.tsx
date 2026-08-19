'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

export default function LoginPage() {
  const router = useRouter();
  const { login, register } = useAuthStore();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: 'admin@personalai.com',
    password: 'admin123'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData.username, formData.email, formData.password);
      }
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || '操作失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">🧠</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Personal AI OS</h1>
          <p className="text-gray-500 mt-2">个人认知操作系统</p>
        </div>

        {/* 切换标签 */}
        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 rounded-md transition-all duration-200 ${
              isLogin ? 'bg-white shadow text-blue-600 font-medium' : 'text-gray-600'
            }`}
          >
            登录
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 rounded-md transition-all duration-200 ${
              !isLogin ? 'bg-white shadow text-blue-600 font-medium' : 'text-gray-600'
            }`}
          >
            注册
          </button>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm animate-fade-in">
            {error}
          </div>
        )}

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div className="animate-slide-up">
              <label className="label">用户名</label>
              <input
                type="text"
                value={formData.username}
                onChange={e => setFormData({ ...formData, username: e.target.value })}
                className="input"
                placeholder="请输入用户名"
                required={!isLogin}
              />
            </div>
          )}

          <div className="animate-slide-up" style={{animationDelay: '50ms'}}>
            <label className="label">邮箱</label>
            <input
              type="email"
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
              className="input"
              placeholder="请输入邮箱"
              required
            />
          </div>

          <div className="animate-slide-up" style={{animationDelay: '100ms'}}>
            <label className="label">密码</label>
            <input
              type="password"
              value={formData.password}
              onChange={e => setFormData({ ...formData, password: e.target.value })}
              className="input"
              placeholder="请输入密码"
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn btn-primary py-3 animate-slide-up"
            style={{animationDelay: '150ms'}}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                处理中...
              </span>
            ) : (
              isLogin ? '登录' : '注册'
            )}
          </button>
        </form>

        {/* 底部提示 */}
        <p className="text-center text-gray-500 text-sm mt-6">
          {isLogin ? '还没有账号？' : '已有账号？'}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:text-blue-700 font-medium ml-1"
          >
            {isLogin ? '立即注册' : '去登录'}
          </button>
        </p>
      </div>
    </div>
  );
}
