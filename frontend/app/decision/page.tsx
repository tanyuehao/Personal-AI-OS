'use client';

import { useState, useEffect } from 'react';
import { decisionApi, cognitiveApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Decision {
  decision_id: string;
  problem: string;
  background?: string;
  options?: string[];
  choice?: string;
  reasoning?: string;
  risk?: string;
  expected_result?: string;
  actual_result?: string;
  lesson?: string;
  category?: string;
  created_at: string;
}

interface Belief {
  belief_id: string;
  topic: string;
  content: string;
  confidence: number;
  status: string;
  created_at: string;
}

interface TimelineItem {
  belief_id: string;
  topic: string;
  content: string;
  confidence: number;
  status: string;
  created_at: string;
  change_count: number;
  history: Array<{
    old_content: string;
    new_content: string;
    change_reason?: string;
    created_at: string;
  }>;
}

export default function DecisionCenterPage() {
  const [activeTab, setActiveTab] = useState<'decisions' | 'beliefs' | 'timeline'>('decisions');
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [beliefs, setBeliefs] = useState<Belief[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newDecision, setNewDecision] = useState({
    problem: '', background: '', options: [] as string[],
    choice: '', reasoning: '', risk: '', category: ''
  });

  useEffect(() => {
    loadDecisions();
    loadBeliefs();
    loadTimeline();
  }, []);

  const loadDecisions = async () => {
    try {
      const response = await decisionApi.list();
      setDecisions(response.data.items);
    } catch (error) { toast.error('加载决策失败'); }
  };

  const loadBeliefs = async () => {
    try {
      const response = await cognitiveApi.listBeliefs();
      setBeliefs(response.data.items);
    } catch (error) { toast.error('加载观点失败'); }
  };

  const loadTimeline = async () => {
    try {
      const response = await cognitiveApi.getTimeline();
      setTimeline(response.data.timeline);
    } catch (error) { toast.error('加载时间线失败'); }
  };

  const handleCreateDecision = async () => {
    if (!newDecision.problem.trim()) return;
    try {
      await decisionApi.create(newDecision);
      setNewDecision({ problem: '', background: '', options: [], choice: '', reasoning: '', risk: '', category: '' });
      setIsCreating(false);
      toast.success('决策已记录');
      await loadDecisions();
    } catch (error) { toast.error('创建失败'); }
  };

  const handleDeleteDecision = async (id: string) => {
    if (!confirm('确定删除？')) return;
    try {
      await decisionApi.delete(id);
      toast.success('已删除');
      await loadDecisions();
    } catch (error) { toast.error('删除失败'); }
  };

  const addOption = () => setNewDecision({ ...newDecision, options: [...newDecision.options, ''] });
  const updateOption = (i: number, v: string) => { const o = [...newDecision.options]; o[i] = v; setNewDecision({ ...newDecision, options: o }); };
  const removeOption = (i: number) => setNewDecision({ ...newDecision, options: newDecision.options.filter((_, idx) => idx !== i) });

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">🎯 决策中心</h1>
          {activeTab === 'decisions' && (
            <button onClick={() => setIsCreating(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              + 记录决策
            </button>
          )}
        </div>

        {/* 标签页 */}
        <div className="flex gap-4 mb-6">
          {[
            { key: 'decisions' as const, label: '🎯 决策记录', count: decisions.length },
            { key: 'beliefs' as const, label: '💭 观点管理', count: beliefs.length },
            { key: 'timeline' as const, label: '📈 观点时间线', count: timeline.length },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-6 py-2 rounded-lg font-medium ${
                activeTab === tab.key ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* 创建表单 */}
        {isCreating && activeTab === 'decisions' && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">记录新决策</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">问题/背景 *</label>
                <textarea value={newDecision.problem} onChange={e => setNewDecision({ ...newDecision, problem: e.target.value })} className="w-full border rounded-lg p-2" rows={3} placeholder="描述你面临的决策问题..." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">备选方案</label>
                {newDecision.options.map((option, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input type="text" value={option} onChange={e => updateOption(index, e.target.value)} className="flex-1 border rounded-lg p-2" placeholder={`方案 ${index + 1}`} />
                    <button onClick={() => removeOption(index)} className="text-red-600 hover:text-red-800">删除</button>
                  </div>
                ))}
                <button onClick={addOption} className="text-blue-600 hover:text-blue-800 text-sm">+ 添加方案</button>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">最终选择</label>
                <input type="text" value={newDecision.choice} onChange={e => setNewDecision({ ...newDecision, choice: e.target.value })} className="w-full border rounded-lg p-2" placeholder="你选择了什么？" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">选择理由</label>
                <textarea value={newDecision.reasoning} onChange={e => setNewDecision({ ...newDecision, reasoning: e.target.value })} className="w-full border rounded-lg p-2" rows={2} placeholder="为什么这样选择？" />
              </div>
              <div className="flex gap-4">
                <button onClick={handleCreateDecision} className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">保存</button>
                <button onClick={() => setIsCreating(false)} className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300">取消</button>
              </div>
            </div>
          </div>
        )}

        {/* 决策列表 */}
        {activeTab === 'decisions' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            {decisions.length === 0 ? (
              <p className="text-gray-500 text-center py-8">还没有决策记录</p>
            ) : (
              <div className="space-y-4">
                {decisions.map(d => (
                  <div key={d.decision_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-lg">{d.problem}</h3>
                        {d.choice && <p className="text-green-600 mt-1">✅ 选择: {d.choice}</p>}
                        {d.reasoning && <p className="text-gray-600 text-sm mt-1">{d.reasoning}</p>}
                        <p className="text-gray-400 text-xs mt-2">{new Date(d.created_at).toLocaleString('zh-CN')}</p>
                      </div>
                      <button onClick={() => handleDeleteDecision(d.decision_id)} className="text-gray-400 hover:text-red-600">🗑️</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 观点管理 */}
        {activeTab === 'beliefs' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            {beliefs.length === 0 ? (
              <p className="text-gray-500 text-center py-8">还没有观点记录</p>
            ) : (
              <div className="space-y-4">
                {beliefs.map(b => (
                  <div key={b.belief_id} className="border rounded-lg p-4">
                    <h3 className="font-medium text-lg">{b.topic}</h3>
                    <p className="text-gray-700 mt-2">{b.content}</p>
                    <div className="flex gap-4 mt-2 text-sm">
                      <span className="text-blue-600">可信度: {(b.confidence * 100).toFixed(0)}%</span>
                      <span className={`px-2 py-1 rounded text-xs ${b.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {b.status === 'ACTIVE' ? '活跃' : '归档'}
                      </span>
                    </div>
                    <p className="text-gray-400 text-xs mt-2">{new Date(b.created_at).toLocaleString('zh-CN')}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 观点时间线 */}
        {activeTab === 'timeline' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            {timeline.length === 0 ? (
              <p className="text-gray-500 text-center py-8">还没有观点数据</p>
            ) : (
              <div className="relative">
                {/* 时间线轴 */}
                <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200" />

                <div className="space-y-8">
                  {timeline.map((item, index) => (
                    <div key={item.belief_id} className="relative pl-16">
                      {/* 时间点 */}
                      <div className={`absolute left-6 w-5 h-5 rounded-full border-4 border-white ${
                        item.change_count > 0 ? 'bg-orange-500' : 'bg-blue-500'
                      }`} style={{ top: '4px' }} />

                      {/* 内容卡片 */}
                      <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-medium text-lg">{item.topic}</h3>
                              {item.change_count > 0 && (
                                <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-xs">
                                  演化 {item.change_count} 次
                                </span>
                              )}
                            </div>
                            <p className="text-gray-700">{item.content}</p>
                            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                              <span>可信度: {(item.confidence * 100).toFixed(0)}%</span>
                              <span>{new Date(item.created_at).toLocaleDateString('zh-CN')}</span>
                            </div>
                          </div>
                          {item.history.length > 0 && (
                            <button
                              onClick={() => setExpandedItem(expandedItem === item.belief_id ? null : item.belief_id)}
                              className="text-blue-600 hover:text-blue-800 text-sm ml-4"
                            >
                              {expandedItem === item.belief_id ? '收起' : '查看变化'}
                            </button>
                          )}
                        </div>

                        {/* 变化历史 */}
                        {expandedItem === item.belief_id && item.history.length > 0 && (
                          <div className="mt-4 pt-4 border-t space-y-3">
                            <h4 className="font-medium text-sm text-gray-600">变化历史</h4>
                            {item.history.map((h, i) => (
                              <div key={i} className="bg-gray-50 rounded p-3 text-sm">
                                <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                                  <span>{new Date(h.created_at).toLocaleString('zh-CN')}</span>
                                  {h.change_reason && <span>• {h.change_reason}</span>}
                                </div>
                                <div className="flex items-start gap-2">
                                  <span className="text-red-600 line-through">{h.old_content}</span>
                                  <span className="text-gray-400">→</span>
                                  <span className="text-green-600">{h.new_content}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
