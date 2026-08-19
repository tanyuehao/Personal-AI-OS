'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [stats, setStats] = useState({
    documents: 0,
    memories: 0,
    conversations: 0,
    beliefs: 0
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    // 加载统计数据
    loadStats();
  }, [isAuthenticated, router]);

  const loadStats = async () => {
    // 模拟加载统计数据
    setStats({
      documents: 12,
      memories: 45,
      conversations: 28,
      beliefs: 8
    });
  };

  const quickActions = [
    { href: '/knowledge', icon: '📚', title: '上传文档', desc: '导入您的知识资料', color: 'from-blue-500 to-blue-600' },
    { href: '/chat', icon: '💬', title: '开始对话', desc: '与 AI 智能问答', color: 'from-purple-500 to-purple-600' },
    { href: '/memory', icon: '🧠', title: '查看记忆', desc: '管理个人记忆', color: 'from-green-500 to-green-600' },
    { href: '/agent', icon: '🤖', title: '使用 Agent', desc: '专业助手服务', color: 'from-pink-500 to-pink-600' },
  ];

  return (
    <div className="p-8 animate-fade-in">
      <div className="max-w-6xl mx-auto">
        {/* 欢迎头部 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            👋 欢迎回来
          </h1>
          <p className="text-gray-500 mt-2">
            这是您的个人认知操作系统控制面板
          </p>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="card animate-slide-up" style={{animationDelay: '0ms'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">文档数量</p>
                <p className="text-3xl font-bold text-blue-600">{stats.documents}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">📄</span>
              </div>
            </div>
          </div>

          <div className="card animate-slide-up" style={{animationDelay: '100ms'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">记忆数量</p>
                <p className="text-3xl font-bold text-green-600">{stats.memories}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🧠</span>
              </div>
            </div>
          </div>

          <div className="card animate-slide-up" style={{animationDelay: '200ms'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">对话次数</p>
                <p className="text-3xl font-bold text-purple-600">{stats.conversations}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">💬</span>
              </div>
            </div>
          </div>

          <div className="card animate-slide-up" style={{animationDelay: '300ms'}}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">观点数量</p>
                <p className="text-3xl font-bold text-yellow-600">{stats.beliefs}</p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">💡</span>
              </div>
            </div>
          </div>
        </div>

        {/* 快捷操作 */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">快捷操作</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => (
              <a
                key={action.href}
                href={action.href}
                className={`bg-gradient-to-r ${action.color} rounded-xl p-6 text-white hover:shadow-lg transition-all duration-300 hover:-translate-y-1 animate-slide-up`}
                style={{animationDelay: `${index * 100}ms`}}
              >
                <div className="text-3xl mb-3">{action.icon}</div>
                <h3 className="text-lg font-semibold">{action.title}</h3>
                <p className="text-white/80 text-sm">{action.desc}</p>
              </a>
            ))}
          </div>
        </div>

        {/* 最近活动 */}
        <div className="card">
          <h2 className="card-header">最近活动</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-xl">📄</span>
              </div>
              <div className="flex-1">
                <p className="font-medium">上传了文档</p>
                <p className="text-sm text-gray-500">2 分钟前</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-xl">💬</span>
              </div>
              <div className="flex-1">
                <p className="font-medium">与 AI 对话</p>
                <p className="text-sm text-gray-500">10 分钟前</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-xl">🧠</span>
              </div>
              <div className="flex-1">
                <p className="font-medium">保存了新记忆</p>
                <p className="text-sm text-gray-500">1 小时前</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
