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
  tags?: string[];
  decision_date?: string;
  created_at: string;
}

interface Belief {
  belief_id: string;
  topic: string;
  content: string;
  confidence: number;
  supporting_evidence?: string[];
  opposing_evidence?: string[];
  status: string;
  created_at: string;
}

export default function DecisionCenterPage() {
  const [activeTab, setActiveTab] = useState<'decisions' | 'beliefs'>('decisions');
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [beliefs, setBeliefs] = useState<Belief[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newDecision, setNewDecision] = useState({
    problem: '',
    background: '',
    options: [] as string[],
    choice: '',
    reasoning: '',
    risk: '',
    category: ''
  });

  useEffect(() => {
    loadDecisions();
    loadBeliefs();
  }, []);

  const loadDecisions = async () => {
    try {
      const response = await decisionApi.list();
      setDecisions(response.data.items);
    } catch (error) {
      toast.error('加载决策失败');
    }
  };

  const loadBeliefs = async () => {
    try {
      const response = await cognitiveApi.listBeliefs();
      setBeliefs(response.data.items);
    } catch (error) {
      toast.error('加载观点失败');
    }
  };

  const handleCreateDecision = async () => {
    if (!newDecision.problem.trim()) return;

    try {
      await decisionApi.create(newDecision);
      setNewDecision({
        problem: '',
        background: '',
        options: [],
        choice: '',
        reasoning: '',
        risk: '',
        category: ''
      });
      setIsCreating(false);
      await loadDecisions();
    } catch (error) {
      toast.error('创建决策失败');
    }
  };

  const handleDeleteDecision = async (decisionId: string) => {
    if (!confirm('确定要删除这条决策记录吗？')) return;

    try {
      await decisionApi.delete(decisionId);
      await loadDecisions();
    } catch (error) {
      toast.error('删除失败');
    }
  };

  const addOption = () => {
    setNewDecision({
      ...newDecision,
      options: [...newDecision.options, '']
    });
  };

  const updateOption = (index: number, value: string) => {
    const newOptions = [...newDecision.options];
    newOptions[index] = value;
    setNewDecision({ ...newDecision, options: newOptions });
  };

  const removeOption = (index: number) => {
    setNewDecision({
      ...newDecision,
      options: newDecision.options.filter((_, i) => i !== index)
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">🎯 决策中心</h1>
          <button
            onClick={() => setIsCreating(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + 记录决策
          </button>
        </div>

        {/* 标签页 */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('decisions')}
            className={`px-6 py-2 rounded-lg font-medium ${
              activeTab === 'decisions'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            🎯 决策记录
          </button>
          <button
            onClick={() => setActiveTab('beliefs')}
            className={`px-6 py-2 rounded-lg font-medium ${
              activeTab === 'beliefs'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            💭 观点管理
          </button>
        </div>

        {/* 创建表单 */}
        {isCreating && activeTab === 'decisions' && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">记录新决策</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">问题/背景 *</label>
                <textarea
                  value={newDecision.problem}
                  onChange={e => setNewDecision({ ...newDecision, problem: e.target.value })}
                  className="w-full border rounded-lg p-2"
                  rows={3}
                  placeholder="描述你面临的决策问题..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">背景信息</label>
                <textarea
                  value={newDecision.background}
                  onChange={e => setNewDecision({ ...newDecision, background: e.target.value })}
                  className="w-full border rounded-lg p-2"
                  rows={2}
                  placeholder="相关的背景信息..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">备选方案</label>
                {newDecision.options.map((option, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={option}
                      onChange={e => updateOption(index, e.target.value)}
                      className="flex-1 border rounded-lg p-2"
                      placeholder={`方案 ${index + 1}`}
                    />
                    <button
                      onClick={() => removeOption(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      删除
                    </button>
                  </div>
                ))}
                <button
                  onClick={addOption}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  + 添加方案
                </button>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">选择的方案</label>
                <input
                  type="text"
                  value={newDecision.choice}
                  onChange={e => setNewDecision({ ...newDecision, choice: e.target.value })}
                  className="w-full border rounded-lg p-2"
                  placeholder="你最终选择的方案"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">判断依据</label>
                <textarea
                  value={newDecision.reasoning}
                  onChange={e => setNewDecision({ ...newDecision, reasoning: e.target.value })}
                  className="w-full border rounded-lg p-2"
                  rows={2}
                  placeholder="为什么做出这个选择..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">风险因素</label>
                <textarea
                  value={newDecision.risk}
                  onChange={e => setNewDecision({ ...newDecision, risk: e.target.value })}
                  className="w-full border rounded-lg p-2"
                  rows={2}
                  placeholder="可能的风险..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">决策类别</label>
                <select
                  value={newDecision.category}
                  onChange={e => setNewDecision({ ...newDecision, category: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="">选择类别</option>
                  <option value="职业">职业</option>
                  <option value="投资">投资</option>
                  <option value="学习">学习</option>
                  <option value="生活">生活</option>
                  <option value="其他">其他</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreateDecision}
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

        {/* 决策列表 */}
        {activeTab === 'decisions' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">决策记录</h2>
            
            {decisions.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                还没有决策记录，开始记录你的第一个重要决策
              </p>
            ) : (
              <div className="space-y-4">
                {decisions.map(decision => (
                  <div
                    key={decision.decision_id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-lg">{decision.problem}</h3>
                        {decision.category && (
                          <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mt-1">
                            {decision.category}
                          </span>
                        )}
                        {decision.choice && (
                          <p className="text-green-600 mt-2">
                            ✅ 选择: {decision.choice}
                          </p>
                        )}
                        {decision.lesson && (
                          <p className="text-gray-600 mt-2">
                            💡 教训: {decision.lesson}
                          </p>
                        )}
                        <p className="text-gray-400 text-sm mt-2">
                          {new Date(decision.created_at).toLocaleString('zh-CN')}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteDecision(decision.decision_id)}
                        className="text-red-600 hover:text-red-800 ml-4"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 观点列表 */}
        {activeTab === 'beliefs' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">观点管理</h2>
            
            {beliefs.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                还没有观点记录
              </p>
            ) : (
              <div className="space-y-4">
                {beliefs.map(belief => (
                  <div
                    key={belief.belief_id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <h3 className="font-medium text-lg">{belief.topic}</h3>
                    <p className="text-gray-700 mt-2">{belief.content}</p>
                    <div className="flex gap-4 mt-2 text-sm">
                      <span className="text-blue-600">
                        可信度: {(belief.confidence * 100).toFixed(0)}%
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        belief.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {belief.status === 'ACTIVE' ? '活跃' : '归档'}
                      </span>
                    </div>
                    <p className="text-gray-400 text-xs mt-2">
                      {new Date(belief.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
