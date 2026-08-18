'use client';

import { useState, useEffect } from 'react';
import { memoryApi } from '@/services/api';

interface Memory {
  memory_id: string;
  memory_type: string;
  content: string;
  source?: string;
  importance: number;
  confidence: number;
  frequency: number;
  is_confirmed: string;
  created_at: string;
  updated_at: string;
}

interface MemoryStats {
  total: number;
  FACT: number;
  EXPERIENCE: number;
  OPINION: number;
  DECISION: number;
  PREFERENCE: number;
  avg_importance: number;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [filter, setFilter] = useState<string>('');
  const [isCreating, setIsCreating] = useState(false);
  const [newMemory, setNewMemory] = useState({
    content: '',
    memory_type: 'FACT',
    importance: 0.5
  });

  useEffect(() => {
    loadMemories();
    loadStats();
  }, [filter]);

  const loadMemories = async () => {
    try {
      const response = await memoryApi.list({
        memory_type: filter || undefined,
        limit: 50
      });
      setMemories(response.data.items);
    } catch (error) {
      console.error('加载记忆失败:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await memoryApi.stats();
      setStats(response.data);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  const handleCreate = async () => {
    if (!newMemory.content.trim()) return;

    try {
      await memoryApi.create(newMemory);
      setNewMemory({ content: '', memory_type: 'FACT', importance: 0.5 });
      setIsCreating(false);
      await loadMemories();
      await loadStats();
    } catch (error) {
      console.error('创建记忆失败:', error);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!confirm('确定要删除这条记忆吗？')) return;

    try {
      await memoryApi.delete(memoryId);
      await loadMemories();
      await loadStats();
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const getMemoryTypeInfo = (type: string) => {
    const types: Record<string, { label: string; color: string; icon: string }> = {
      FACT: { label: '事实', color: 'bg-blue-100 text-blue-800', icon: '📌' },
      EXPERIENCE: { label: '经验', color: 'bg-green-100 text-green-800', icon: '💡' },
      OPINION: { label: '观点', color: 'bg-purple-100 text-purple-800', icon: '💭' },
      DECISION: { label: '决策', color: 'bg-orange-100 text-orange-800', icon: '🎯' },
      PREFERENCE: { label: '偏好', color: 'bg-pink-100 text-pink-800', icon: '❤️' }
    };
    return types[type] || { label: type, color: 'bg-gray-100 text-gray-800', icon: '📄' };
  };

  const getImportanceColor = (importance: number) => {
    if (importance >= 0.8) return 'text-red-600';
    if (importance >= 0.6) return 'text-orange-600';
    if (importance >= 0.4) return 'text-yellow-600';
    return 'text-gray-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">🧠 记忆中心</h1>
          <button
            onClick={() => setIsCreating(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + 新建记忆
          </button>
        </div>

        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
              <p className="text-gray-500 text-sm">总记忆数</p>
            </div>
            {Object.entries(stats).filter(([key]) => key !== 'total' && key !== 'avg_importance').map(([key, value]) => {
              const info = getMemoryTypeInfo(key);
              return (
                <div key={key} className="bg-white rounded-lg shadow p-4 text-center">
                  <p className="text-2xl">{info.icon}</p>
                  <p className="text-xl font-bold">{value as number}</p>
                  <p className="text-gray-500 text-sm">{info.label}</p>
                </div>
              );
            })}
          </div>
        )}

        {/* 创建表单 */}
        {isCreating && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">新建记忆</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">记忆类型</label>
                <select
                  value={newMemory.memory_type}
                  onChange={e => setNewMemory({ ...newMemory, memory_type: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="FACT">📌 事实</option>
                  <option value="EXPERIENCE">💡 经验</option>
                  <option value="OPINION">💭 观点</option>
                  <option value="DECISION">🎯 决策</option>
                  <option value="PREFERENCE">❤️ 偏好</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">内容</label>
                <textarea
                  value={newMemory.content}
                  onChange={e => setNewMemory({ ...newMemory, content: e.target.value })}
                  className="w-full border rounded-lg p-2"
                  rows={4}
                  placeholder="输入记忆内容..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  重要程度: {newMemory.importance}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newMemory.importance}
                  onChange={e => setNewMemory({ ...newMemory, importance: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  保存
                </button>
                <button
                  onClick={() => setIsCreating(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 筛选器 */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter('')}
              className={`px-4 py-2 rounded-full text-sm ${
                filter === '' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              全部
            </button>
            {['FACT', 'EXPERIENCE', 'OPINION', 'DECISION', 'PREFERENCE'].map(type => {
              const info = getMemoryTypeInfo(type);
              return (
                <button
                  key={type}
                  onClick={() => setFilter(type)}
                  className={`px-4 py-2 rounded-full text-sm ${
                    filter === type ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {info.icon} {info.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 记忆列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">记忆列表</h2>
          
          {memories.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              还没有记忆，开始创建或通过对话自动生成
            </p>
          ) : (
            <div className="space-y-4">
              {memories.map(memory => {
                const typeInfo = getMemoryTypeInfo(memory.memory_type);
                return (
                  <div
                    key={memory.memory_id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-1 rounded text-xs ${typeInfo.color}`}>
                            {typeInfo.icon} {typeInfo.label}
                          </span>
                          <span className={`text-sm ${getImportanceColor(memory.importance)}`}>
                            重要度: {(memory.importance * 100).toFixed(0)}%
                          </span>
                          <span className="text-sm text-gray-500">
                            可信度: {(memory.confidence * 100).toFixed(0)}%
                          </span>
                          {memory.frequency > 1 && (
                            <span className="text-sm text-gray-500">
                              出现 {memory.frequency} 次
                            </span>
                          )}
                        </div>
                        <p className="text-gray-800">{memory.content}</p>
                        {memory.source && (
                          <p className="text-gray-500 text-sm mt-2">来源: {memory.source}</p>
                        )}
                        <p className="text-gray-400 text-xs mt-2">
                          创建于 {new Date(memory.created_at).toLocaleString('zh-CN')}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDelete(memory.memory_id)}
                        className="text-red-600 hover:text-red-800 ml-4"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
