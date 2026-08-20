'use client';

import { useState, useEffect } from 'react';
import { proactiveApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Insight {
  insight_id: string;
  insight_type: string;
  title: string;
  description: string;
  priority: string;
  category: string;
  action_suggestion: string;
  is_read: boolean;
  created_at: string;
}

interface Prediction {
  prediction_id: string;
  prediction_type: string;
  title: string;
  description: string;
  confidence: number;
  evidence: string[];
  suggested_actions: string[];
}

interface Context {
  current_topic: string | null;
  current_project: string | null;
  recent_documents: Array<{ id: string; name: string; type: string }>;
  recent_topics: string[];
  active_memories: Array<{ id: string; content: string; type: string }>;
  pending_decisions: Array<{ id: string; problem: string }>;
  last_updated: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
};

const TYPE_ICONS: Record<string, string> = {
  knowledge_gap: '📚',
  memory_decay: '🧠',
  decision_pattern: '🎯',
  conflict_detected: '⚠️',
  opportunity: '💡',
  reminder: '⏰',
  trend: '📈',
  recommendation: '✨',
};

export default function ProactivePage() {
  const [context, setContext] = useState<Context | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [trends, setTrends] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [contextRes, insightsRes, trendsRes] = await Promise.all([
        proactiveApi.getContext(),
        proactiveApi.getInsights(),
        proactiveApi.getTrends()
      ]);
      setContext(contextRes.data);
      setInsights(insightsRes.data);
      setTrends(trendsRes.data);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const handleGenerateInsights = async () => {
    setGenerating(true);
    try {
      await proactiveApi.generateInsights();
      toast.success('洞察已生成');
      await loadData();
    } catch (error) {
      toast.error('生成洞察失败');
    }
    setGenerating(false);
  };

  const handleGenerateTrends = async () => {
    setGenerating(true);
    try {
      await proactiveApi.predictTrends();
      toast.success('趋势预测已生成');
      await loadData();
    } catch (error) {
      toast.error('生成趋势失败');
    }
    setGenerating(false);
  };

  const handleDismiss = async (insightId: string) => {
    try {
      await proactiveApi.dismissInsight(insightId);
      setInsights(insights.filter(i => i.insight_id !== insightId));
      toast.success('已忽略');
    } catch (error) {
      toast.error('操作失败');
    }
  };

  const handleMarkRead = async (insightId: string) => {
    try {
      await proactiveApi.markInsightRead(insightId);
      setInsights(insights.map(i =>
        i.insight_id === insightId ? { ...i, is_read: true } : i
      ));
    } catch (error) {
      console.error(error);
    }
  };

  const unreadCount = insights.filter(i => !i.is_read).length;

  if (loading) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">🔮 主动智能</h1>
            <p className="text-gray-500 mt-1">AI 主动发现的信息和建议</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleGenerateInsights}
              disabled={generating}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {generating ? '生成中...' : '🔄 生成洞察'}
            </button>
            <button
              onClick={handleGenerateTrends}
              disabled={generating}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {generating ? '生成中...' : '📈 预测趋势'}
            </button>
          </div>
        </div>

        {/* 当前上下文 */}
        {context && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">📍 当前上下文</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-500">当前话题</div>
                <div className="font-medium truncate">{context.current_topic || '无'}</div>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-sm text-gray-500">最近文档</div>
                <div className="font-medium">{context.recent_documents.length} 个</div>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="text-sm text-gray-500">活跃记忆</div>
                <div className="font-medium">{context.active_memories.length} 条</div>
              </div>
              <div className="p-3 bg-yellow-50 rounded-lg">
                <div className="text-sm text-gray-500">待决策</div>
                <div className="font-medium">{context.pending_decisions.length} 个</div>
              </div>
            </div>
            {context.recent_topics.length > 0 && (
              <div className="mt-4">
                <div className="text-sm text-gray-500 mb-2">最近话题</div>
                <div className="flex flex-wrap gap-2">
                  {context.recent_topics.slice(0, 5).map((topic, i) => (
                    <span key={i} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 主动洞察 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">🔔 主动洞察</h2>
              {unreadCount > 0 && (
                <span className="px-2 py-1 bg-red-500 text-white text-xs rounded-full">
                  {unreadCount} 条未读
                </span>
              )}
            </div>

            {insights.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📭</div>
                <p>暂无洞察</p>
                <p className="text-sm">点击"生成洞察"让 AI 分析你的数据</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {insights.map(insight => (
                  <div
                    key={insight.insight_id}
                    className={`p-4 rounded-lg border ${
                      insight.is_read ? 'bg-gray-50 border-gray-200' : 'bg-white border-blue-200'
                    } ${PRIORITY_COLORS[insight.priority] || ''}`}
                    onClick={() => handleMarkRead(insight.insight_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2">
                        <span className="text-xl">
                          {TYPE_ICONS[insight.insight_type] || '📌'}
                        </span>
                        <div>
                          <h3 className="font-medium">{insight.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                          {insight.action_suggestion && (
                            <p className="text-sm text-blue-600 mt-2">
                              💡 {insight.action_suggestion}
                            </p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDismiss(insight.insight_id); }}
                        className="text-gray-400 hover:text-red-500 ml-2"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="text-xs text-gray-400 mt-2">
                      {insight.category} · {new Date(insight.created_at).toLocaleDateString('zh-CN')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 趋势预测 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">📈 趋势预测</h2>

            {trends.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">🔮</div>
                <p>暂无趋势预测</p>
                <p className="text-sm">点击"预测趋势"让 AI 分析你的数据</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {trends.map(trend => (
                  <div key={trend.prediction_id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium">{trend.title}</h3>
                      <span className="text-sm text-gray-500">
                        置信度: {(trend.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{trend.description}</p>

                    {trend.evidence.length > 0 && (
                      <div className="mb-3">
                        <div className="text-xs text-gray-500 mb-1">依据：</div>
                        {trend.evidence.map((e, i) => (
                          <div key={i} className="text-xs text-gray-600 ml-2">• {e}</div>
                        ))}
                      </div>
                    )}

                    {trend.suggested_actions.length > 0 && (
                      <div>
                        <div className="text-xs text-gray-500 mb-1">建议操作：</div>
                        {trend.suggested_actions.map((a, i) => (
                          <div key={i} className="text-xs text-blue-600 ml-2">→ {a}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
