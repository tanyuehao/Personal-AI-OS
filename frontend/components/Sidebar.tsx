'use client';

import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

const menuItems = [
  { path: '/dashboard', name: '控制面板', icon: '🏠' },
  { path: '/knowledge', name: '知识库', icon: '📚' },
  { path: '/chat', name: 'AI 聊天', icon: '💬' },
  { path: '/memory', name: '记忆', icon: '🧠' },
  { path: '/graph', name: '知识图谱', icon: '🔗' },
  { path: '/agent', name: 'Agent', icon: '🤖' },
  { path: '/multimodal', name: '多模态', icon: '📷' },
  { path: '/decision', name: '决策中心', icon: '🎯' },
  { path: '/settings', name: '设置', icon: '⚙️' },
  { path: '/usage', name: '使用量', icon: '📊' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuthStore();

  if (!isAuthenticated || pathname === '/login') {
    return null;
  }

  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4 flex flex-col relative">
      <div className="mb-8">
        <h1 className="text-xl font-bold">🧠 Personal AI OS</h1>
        <p className="text-gray-400 text-sm mt-1">个人认知操作系统</p>
      </div>

      <nav className="space-y-1 flex-1">
        {menuItems.map(item => (
          <a
            key={item.path}
            href={item.path}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
              pathname === item.path
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <span className="text-xl">{item.icon}</span>
            <span>{item.name}</span>
          </a>
        ))}
      </nav>

      <div className="mt-4">
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 transition"
        >
          <span className="text-xl">🚪</span>
          <span>退出登录</span>
        </button>
        <p className="text-xs text-gray-500 mt-2 text-center">版本 0.1.0</p>
      </div>
    </div>
  );
}
