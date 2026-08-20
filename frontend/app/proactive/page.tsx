'use client';

import { useState, useEffect } from 'react';
import { proactiveApi, predictionApi, contextApi } from '@/services/api';
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
  time_horizon: string;
}

interface Context {
  current_session: any;
  active_focus: Array<{ name: string; type: string; priority: number }>;
  recent_activities: Array<{ type: string; action: string; time: string }>;
  current_mood: string;
  energy_level: number;
  suggestions: string[];
}

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-50 border-red-200 text-red-800',
  medium: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  low: 'bg-blue-50 border-blue-200 text-blue-800',
};

const TYPE_ICONS: Record<string, string> = {
  knowledge_gap: '📚', memory_decay: '🧠', decision_pattern: '🎯',
  conflict_detected: '⚠️', opportunity: '💡', reminder: '⏰',
  trend: '📈', recommendation: '✨',
  next_action: '🎯', information_need: '📚', decision_pending: '📋',
  learning_opportunity: '📖', risk_alert: '⚠️', optimization: '💡',
};

const MOOD_EMOJI: Record<string, string> = {
  focused: '🎯', engaged: '💪', relaxed: '😌', tired: '😴', neutral: '😐',
};

export default function ProactivePage() {
  const [context, setContext] = useState<Context | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [trends, setTrends] = useState<Prediction[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [contextRes, insightsRes, trendsRes, predsRes] = await Promise.all([
        proactiveApi.getContext(),
        proactiveApi.getInsights(),
        proactiveApi.getTrends(),
        predictionApi.getPredictions()
      ]);
      setContext(contextRes.data);
      setInsights(insightsRes.data);
      setTrends(trendsRes.data);
      setPredictions(predsRes.data);
    } catch (error) { console.error(error); }
    setLoading(false);
  };

  const handleGenerateInsights = async () => {
    setGenerating(true);
    try {
      await proactiveApi.generateInsights();
      toast.success('洞察已生成');
      await loadData();
    } catch (error) { toast.error('生成洞察失败'); }
    setGenerating(false);
  };

  const handleGeneratePredictions = async () => {
    setGenerating(true);
    try {
      await predictionApi.predict();
      toast.success('预测已生成');
      await loadData();
    } catch (error) { toast.error('生成预测失败'); }
    setGenerating(false);
  };

  const handleDismiss = async (insightId: string) => {
    try {
      await proactiveApi.dismissInsight(insightId);
      setInsights(insights.filter(i => i.insight_id !== insightId));
      toast.success('已忽略');
    } catch (error) { toast.error('操作失败'); }
  };

  if (loading) return <div className="min-h-screen bg-gray-50 flex items-center justify-center">加载中...</div>;

  const unreadCount = insights.filter(i => !i.is_read).length;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">🔮 主动智能</h1>
            <p className="text-gray-500 mt-1">AI 主动发现的信息和建议</p>
          </div>
          <div className="flex gap-3">
            <button onClick={handleGenerateInsights} disabled={generating}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {generating ? '生成中...' : '🔄 生成洞察'}
            </button>
            <button onClick={handleGeneratePredictions} disabled={generating}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50">
              {generating ? '生成中...' : '📈 生成预测'}
            </button>
          </div>
        </div>

        {/* 当前状态卡片 */}
        {context && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-3xl mb-2">{MOOD_EMOJI[context.current_mood] || '😐'}</div>
              <div className="text-sm text-gray-500">当前状态</div>
              <div className="font-medium">{context.current_mood}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-3xl mb-2">⚡</div>
              <div className="text-sm text-gray-500">精力水平</div>
              <div className="font-medium">{((context.energy_level || 0) * 100).toFixed(0)}%</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-3xl mb-2">🎯</div>
              <div className="text-sm text-gray-500">关注焦点</div>
              <div className="font-medium">{(context.active_focus || []).length} 个</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-3xl mb-2">🔔</div>
              <div className="text-sm text-gray-500">未读洞察</div>
              <div className="font-medium">{unreadCount}</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-3xl mb-2">📈</div>
              <div className="text-sm text-gray-500">需求预测</div>
              <div className="font-medium">{predictions.length}</div>
            </div>
          </div>
        )}

        {/* 焦点和建议 */}
        {context && (context.active_focus || []).length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <h3 className="font-semibold mb-3">🎯 当前焦点</h3>
            <div className="flex flex-wrap gap-2">
              {(context.active_focus || []).map((f, i) => (
                <span key={i} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                  {f.name} ({(f.priority * 100).toFixed(0)}%)
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 洞察 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">🔔 主动洞察</h2>
            {insights.length === 0 ? (
              <p className="text-center py-8 text-gray-500">暂无洞察</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {insights.map(insight => (
                  <div key={insight.insight_id} className={`p-3 rounded-lg border ${PRIORITY_COLORS[insight.priority] || ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2">
                        <span>{TYPE_ICONS[insight.insight_type] || '📌'}</span>
                        <div>
                          <h4 className="font-medium text-sm">{insight.title}</h4>
                          <p className="text-xs opacity-75 mt-1">{insight.description}</p>
                        </div>
                      </div>
                      <button onClick={() => handleDismiss(insight.insight_id)} className="text-gray-400 hover:text-red-500 ml-2">✕</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 预测 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">📈 需求预测</h2>
            {predictions.length === 0 ? (
              <p className="text-center py-8 text-gray-500">暂无预测</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {predictions.map(pred => (
                  <div key={pred.prediction_id} className="border rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <h4 className="font-medium text-sm">{pred.title}</h4>
                      <span className="text-xs text-gray-500">{(pred.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{pred.description}</p>
                    {pred.suggested_actions.length > 0 && (
                      <div className="mt-2">
                        {pred.suggested_actions.slice(0, 2).map((a, i) => (
                          <div key={i} className="text-xs text-blue-600">→ {a}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 趋势 */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">📊 趋势预测</h2>
          {trends.length === 0 ? (
            <p className="text-center py-8 text-gray-500">暂无趋势</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {trends.map(trend => (
                <div key={trend.prediction_id} className="border rounded-lg p-4">
                  <h4 className="font-medium">{trend.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{trend.description}</p>
                  <div className="mt-2 text-xs text-gray-500">置信度: {(trend.confidence * 100).toFixed(0)}%</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
