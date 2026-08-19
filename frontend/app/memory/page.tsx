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

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [isCreating, setIsCreating] = useState(false);
  const [newMemory, setNewMemory] = useState({
    content: '',
    memory_type: 'FACT',
    importance: 0.5
  });

  useEffect(() => {
    loadMemories();
  }, [filter]);

  const loadMemories = async () => {
    try {
      const response = await memoryApi.list({
        memory_type: filter || undefined,
        limit: 50
      });
      setMemories(response.data.items || []);
    } catch (error) {
      toast.error('加载记忆失败');
    }
  };

  const handleCreate = async () => {
    if (!newMemory.content.trim()) return;
    try {
      await memoryApi.create(newMemory);
      toast.success('创建成功');
      setNewMemory({ content: '', memory_type: 'FACT', importance: 0.5 });
      setIsCreating(false);
      await loadMemories();
    } catch (error) {
      toast.error('创建失败');
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!confirm('确定要删除这条记忆吗？')) return;
    try {
      await memoryApi.delete(memoryId);
      toast.success('删除成功');
      await loadMemories();
    } catch (error) {
      toast.error('删除失败');
    }
  };

  return (
    <div className="p-8 animate-fade-in">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">🧠 记忆中心</h1>
          <button onClick={() => setIsCreating(true)} className="btn btn-primary">
            + 新建记忆
          </button>
        </div>

        {isCreating && (
          <div className="card mb-6 animate-slide-up">
            <h2 className="card-header">新建记忆</h2>
            <div className="space-y-4">
              <div>
                <label className="label">记忆类型</label>
                <select
                  value={newMemory.memory_type}
                  onChange={e => setNewMemory({ ...newMemory, memory_type: e.target.value })}
                  className="input"
                >
                  <option value="FACT">📌 事实</option>
                  <option value="EXPERIENCE">💡 经验</option>
                  <option value="OPINION">💭 观点</option>
                  <option value="DECISION">🎯 决策</option>
                  <option value="PREFERENCE">❤️ 偏好</option>
                </select>
              </div>
              <div>
                <label className="label">内容</label>
                <textarea
                  value={newMemory.content}
                  onChange={e => setNewMemory({ ...newMemory, content: e.target.value })}
                  className="input"
                  rows={4}
                  placeholder="输入记忆内容..."
                />
              </div>
              <div className="flex gap-2">
                <button onClick={handleCreate} className="btn btn-primary">保存</button>
                <button onClick={() => setIsCreating(false)} className="btn btn-secondary">取消</button>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-2 mb-6">
          <button onClick={() => setFilter('')} className={`px-4 py-2 rounded-full text-sm ${filter === '' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>全部</button>
          {['FACT', 'EXPERIENCE', 'OPINION', 'DECISION', 'PREFERENCE'].map(type => (
            <button key={type} onClick={() => setFilter(type)} className={`px-4 py-2 rounded-full text-sm ${filter === type ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
              {TYPE_LABELS[type]}
            </button>
          ))}
        </div>

        <div className="card">
          <h2 className="card-header">记忆列表</h2>
          {memories.length === 0 ? (
            <div className="text-center py-12"><div className="text-6xl mb-4">🧠</div><p className="text-gray-500">暂无记忆</p></div>
          ) : (
            <div className="space-y-4">
              {memories.map(memory => (
                <div key={memory.memory_id} className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`badge ${TYPE_COLORS[memory.memory_type]}`}>{TYPE_LABELS[memory.memory_type]}</span>
                        <span className={`badge ${memory.is_confirmed === 'CONFIRMED' ? 'bg-green-100 text-green-800' : memory.is_confirmed === 'PENDING' ? 'bg-orange-100 text-orange-800' : 'bg-red-100 text-red-800'}`}>
                          {memory.is_confirmed === 'CONFIRMED' ? '已确认' : memory.is_confirmed === 'PENDING' ? '待确认' : '已拒绝'}
                        </span>
                      </div>
                      <p className="text-gray-800">{memory.content}</p>
                    </div>
                    <button onClick={() => handleDelete(memory.memory_id)} className="btn btn-ghost text-red-600 text-sm">删除</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
