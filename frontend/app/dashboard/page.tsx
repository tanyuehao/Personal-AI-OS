'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    setUser({ username: 'User' });
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">控制面板</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <a href="/knowledge" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
            <div className="text-4xl mb-4">📚</div>
            <h2 className="text-xl font-semibold">知识库</h2>
            <p className="text-gray-500 mt-2">上传和管理文档</p>
          </a>
          
          <a href="/chat" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
            <div className="text-4xl mb-4">💬</div>
            <h2 className="text-xl font-semibold">AI 聊天</h2>
            <p className="text-gray-500 mt-2">与 AI 对话</p>
          </a>
          
          <a href="/memory" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
            <div className="text-4xl mb-4">🧠</div>
            <h2 className="text-xl font-semibold">记忆</h2>
            <p className="text-gray-500 mt-2">管理你的记忆</p>
          </a>
          
          <a href="/settings" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
            <div className="text-4xl mb-4">⚙️</div>
            <h2 className="text-xl font-semibold">设置</h2>
            <p className="text-gray-500 mt-2">配置 API 密钥</p>
          </a>
        </div>

        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">快速开始</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-600">
            <li>前往 <a href="/settings" className="text-blue-600 hover:underline">设置</a> 页面配置你的 API Key</li>
            <li>选择语言模型（推荐 DeepSeek-V4-Flash）</li>
            <li>前往 <a href="/knowledge" className="text-blue-600 hover:underline">知识库</a> 上传你的文档</li>
            <li>前往 <a href="/chat" className="text-blue-600 hover:underline">AI 聊天</a> 开始提问</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
