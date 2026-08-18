'use client';

import { useState, useEffect } from 'react';
import { memoryApi } from '@/services/api';
import toast from 'react-hot-toast';

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
}

const TYPE_COLORS: Record<string, string> = {
  FACT: 'bg-blue-100 text-blue-800',
  EXPERIENCE: 'bg-green-100 text-green-800',
  OPINION: 'bg-purple-100 text-purple-800',
  DECISION: 'bg-yellow-100 text-yellow-800',
  PREFERENCE: 'bg-pink-100 text-pink-800',
};

const TYPE_LABELS: Record<string, string> = {
  FACT: '事实',
  EXPERIENCE: '经验',
  OPINION: '观点',
  DECISION: '决策',
  PREFERENCE: '偏好',
};

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-orange-100 text-orange-800',
  CONFIRMED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
};

const STATUS_LABELS: Record<string, string> = {
  PENDING: '待确认',
  CONFIRMED: '已确认',
  REJECTED: '已拒绝',
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [candidates, setCandidates] = useState<Memory[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [filter, setFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isCreating, setIsCreating] = useState(false);
  const [newMemory, setNewMemory] = useState({
    content: '',
    memory_type: 'FACT',
    importance: 0.5
  });
  const [activeTab, setActiveTab] = useState<'all' | 'candidates'>('all');

  useEffect(() => {
    loadMemories();
    loadStats();
    loadCandidates();
  }, [filter, statusFilter]);

  const loadMemories = async () => {
    try {
      const response = await memoryApi.list({
        memory_type: filter || undefined,
        limit: 50
      });
      setMemories(response.data.items);
    } catch (error) {
      toast.error('加载记忆失败');
    }
  };

  const loadCandidates = async () => {
    try {
      const response = await memoryApi.candidates({ limit: 50 });
      setCandidates(response.data.items);
    } catch (error) {
      toast.error('加载候选记忆失败');
    }
  };

  const loadStats = async () => {
    try {
      const response = await memoryApi.stats();
      setStats(response.data);
    } catch (error) {
      toast.error('加载统计失败');
    }
  };

  const handleCreate = async () => {
    if (!newMemory.content.trim()) {
      toast.error('请输入记忆内容');
      return;
    }

    setIsCreating(true);
    try {
      await memoryApi.create({
        content: newMemory.content,
        memory_type: newMemory.memory_type,
        importance: newMemory.importance
      });
      setNewMemory({ content: '', memory_type: 'FACT', importance: 0.5 });
      toast.success('记忆已创建');
      await loadMemories();
      await loadStats();
    } catch (error) {
      toast.error('创建记忆失败');
    }
    setIsCreating(false);
  };

  const handleConfirm = async (id: string) => {
    try {
      await memoryApi.confirm(id);
      toast.success('已确认');
      await loadCandidates();
      await loadMemories();
      await loadStats();
    } catch (error) {
      toast.error('确认失败');
    }
  };

  const handleReject = async (id: string) => {
    try {
      await memoryApi.reject(id);
      toast.success('已拒绝');
      await loadCandidates();
      await loadStats();
    } catch (error) {
      toast.error('拒绝失败');
    }
  };

  const handleConfirmAll = async () => {
    if (candidates.length === 0) return;
    try {
      const result = await memoryApi.confirmAll();
      toast.success(`已确认 ${result.data.confirmed} 条记忆`);
      await loadCandidates();
      await loadMemories();
      await loadStats();
    } catch (error) {
      toast.error('批量确认失败');
    }
  };

  const handleRejectAll = async () => {
    if (candidates.length === 0) return;
    try {
      const result = await memoryApi.rejectAll();
      toast.success(`已拒绝 ${result.data.rejected} 条记忆`);
      await loadCandidates();
      await loadStats();
    } catch (error) {
      toast.error('批量拒绝失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await memoryApi.delete(id);
      toast.success('已删除');
      await loadMemories();
      await loadCandidates();
      await loadStats();
    } catch (error) {
      toast.error('删除失败');
    }
  };

  const displayedMemories = activeTab === 'candidates' ? candidates : memories;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">🧠 记忆管理</h1>

        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-500">总记忆</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-orange-600">{candidates.length}</div>
              <div className="text-sm text-gray-500">待确认</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{stats.FACT + stats.EXPERIENCE + stats.OPINION + stats.DECISION + stats.PREFERENCE}</div>
              <div className="text-sm text-gray-500">已确认</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-gray-600">{stats.avg_importance?.toFixed(2) || '0'}</div>
              <div className="text-sm text-gray-500">平均重要性</div>
            </div>
          </div>
        )}

        <div className="flex gap-4">
          {/* 左侧：创建记忆 */}
          <div className="w-80">
            <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
              <h2 className="font-semibold mb-3">创建记忆</h2>
              <textarea
                value={newMemory.content}
                onChange={e => setNewMemory({...newMemory, content: e.target.value})}
                placeholder="输入记忆内容..."
                className="w-full border rounded-lg p-2 text-sm mb-3"
                rows={3}
              />
              <select
                value={newMemory.memory_type}
                onChange={e => setNewMemory({...newMemory, memory_type: e.target.value})}
                className="w-full border rounded-lg p-2 text-sm mb-3"
              >
                {Object.entries(TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
              <div className="mb-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>重要性</span>
                  <span>{newMemory.importance}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newMemory.importance}
                  onChange={e => setNewMemory({...newMemory, importance: parseFloat(e.target.value)})}
                  className="w-full"
                />
              </div>
              <button
                onClick={handleCreate}
                disabled={isCreating}
                className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {isCreating ? '创建中...' : '创建'}
              </button>
            </div>

            {/* 类型图例 */}
            <div className="bg-white rounded-lg shadow-sm p-4">
              <h3 className="font-semibold text-sm mb-2">记忆类型</h3>
              <div className="space-y-2">
                {Object.entries(TYPE_LABELS).map(([key, label]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${TYPE_COLORS[key]}`}>{label}</span>
                    <span className="text-xs text-gray-500">{stats?.[key] || 0}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 右侧：记忆列表 */}
          <div className="flex-1">
            {/* 标签页 */}
            <div className="bg-white rounded-lg shadow-sm mb-4">
              <div className="flex border-b">
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-4 py-3 text-sm font-medium ${
                    activeTab === 'all' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  所有记忆 ({memories.length})
                </button>
                <button
                  onClick={() => setActiveTab('candidates')}
                  className={`px-4 py-3 text-sm font-medium ${
                    activeTab === 'candidates' ? 'border-b-2 border-orange-500 text-orange-600' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  待确认 ({candidates.length})
                </button>
              </div>

              {/* 候选操作栏 */}
              {activeTab === 'candidates' && candidates.length > 0 && (
                <div className="flex items-center justify-between px-4 py-2 bg-orange-50">
                  <span className="text-sm text-orange-700">
                    有 {candidates.length} 条记忆待确认
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={handleConfirmAll}
                      className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                    >
                      全部确认
                    </button>
                    <button
                      onClick={handleRejectAll}
                      className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                    >
                      全部拒绝
                    </button>
                  </div>
                </div>
              )}

              {/* 筛选器 */}
              {activeTab === 'all' && (
                <div className="px-4 py-2 border-b flex gap-2">
                  <select
                    value={filter}
                    onChange={e => setFilter(e.target.value)}
                    className="border rounded px-2 py-1 text-sm"
                  >
                    <option value="">全部类型</option>
                    {Object.entries(TYPE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* 记忆列表 */}
            <div className="space-y-3">
              {displayedMemories.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-500">
                  {activeTab === 'candidates' ? '没有待确认的记忆' : '暂无记忆'}
                </div>
              ) : (
                displayedMemories.map(memory => (
                  <div
                    key={memory.memory_id}
                    className={`bg-white rounded-lg shadow-sm p-4 ${
                      memory.is_confirmed === 'PENDING' ? 'border-l-4 border-orange-400' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${TYPE_COLORS[memory.memory_type]}`}>
                            {TYPE_LABELS[memory.memory_type]}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[memory.is_confirmed]}`}>
                            {STATUS_LABELS[memory.is_confirmed]}
                          </span>
                        </div>
                        <p className="text-gray-800">{memory.content}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span>重要性: {(memory.importance * 100).toFixed(0)}%</span>
                          <span>可信度: {(memory.confidence * 100).toFixed(0)}%</span>
                          <span>{new Date(memory.created_at).toLocaleDateString('zh-CN')}</span>
                        </div>
                      </div>

                      {/* 操作按钮 */}
                      <div className="flex items-center gap-2 ml-4">
                        {memory.is_confirmed === 'PENDING' && (
                          <>
                            <button
                              onClick={() => handleConfirm(memory.memory_id)}
                              className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                            >
                              确认
                            </button>
                            <button
                              onClick={() => handleReject(memory.memory_id)}
                              className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                            >
                              拒绝
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDelete(memory.memory_id)}
                          className="text-gray-400 hover:text-red-600 text-sm"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
