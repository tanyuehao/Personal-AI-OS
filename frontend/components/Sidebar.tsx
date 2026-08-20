'use client';

import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useState } from 'react';

const menuItems = [
  { path: '/dashboard', name: '控制面板', icon: '🏠', color: 'text-blue-500' },
  { path: '/proactive', name: '主动智能', icon: '🔮', color: 'text-violet-500' },
  { path: '/knowledge', name: '知识库', icon: '📚', color: 'text-green-500' },
  { path: '/chat', name: 'AI 聊天', icon: '💬', color: 'text-purple-500' },
  { path: '/memory', name: '记忆', icon: '🧠', color: 'text-yellow-500' },
  { path: '/graph', name: '知识图谱', icon: '🔗', color: 'text-indigo-500' },
  { path: '/agent', name: 'Agent', icon: '🤖', color: 'text-pink-500' },
  { path: '/multimodal', name: '多模态', icon: '📷', color: 'text-orange-500' },
  { path: '/decision', name: '决策中心', icon: '🎯', color: 'text-red-500' },
  { path: '/decision-style', name: '决策风格', icon: '🧬', color: 'text-emerald-500' },
  { path: '/settings', name: '设置', icon: '⚙️', color: 'text-gray-500' },
  { path: '/usage', name: '使用量', icon: '📊', color: 'text-cyan-500' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuthStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!isAuthenticated || pathname === '/login') {
    return null;
  }

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-64'} bg-gradient-to-b from-gray-900 to-gray-800 text-white min-h-screen p-4 flex flex-col relative transition-all duration-300`}>
      {/* Logo */}
      <div className="mb-8 flex items-center justify-between">
        {!isCollapsed && (
          <div>
            <h1 className="text-xl font-bold">🧠 Personal AI OS</h1>
            <p className="text-gray-400 text-xs mt-1">个人认知操作系统</p>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>

      {/* 导航菜单 */}
      <nav className="space-y-1 flex-1">
        {menuItems.map(item => (
          <a
            key={item.path}
            href={item.path}
            className={`nav-item ${pathname === item.path ? 'active' : ''}`}
            title={isCollapsed ? item.name : undefined}
          >
            <span className={`text-xl ${pathname === item.path ? item.color : ''}`}>
              {item.icon}
            </span>
            {!isCollapsed && <span>{item.name}</span>}
          </a>
        ))}
      </nav>

      {/* 用户信息 */}
      <div className="mt-4">
        {!isCollapsed && (
          <div className="bg-gray-800 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium">U</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">用户</p>
                <p className="text-xs text-gray-400">v0.1.0</p>
              </div>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
          title={isCollapsed ? '退出登录' : undefined}
        >
          <span className="text-xl">🚪</span>
          {!isCollapsed && <span>退出登录</span>}
        </button>
      </div>
    </div>
  );
}
