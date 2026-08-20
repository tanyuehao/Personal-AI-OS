'use client';

import { useState, useEffect } from 'react';
import { learningApi } from '@/services/api';
import toast from 'react-hot-toast';

interface LearningEvent {
  event_id: string;
  event_type: string;
  source: string;
  content: string;
  impact: number;
  created_at: string;
}

interface LearningStats {
  total_learning_events: number;
  total_preferences: number;
  total_corrections: number;
  total_feedbacks: number;
  average_feedback_rating: number;
}

const EVENT_ICONS: Record<string, string> = {
  new_knowledge: '📚', preference_learned: '⭐', correction_applied: '✏️',
  pattern_discovered: '🔍', model_updated: '🔄', feedback_received: '💬',
};

const EVENT_COLORS: Record<string, string> = {
  new_knowledge: 'bg-blue-100 text-blue-800',
  preference_learned: 'bg-yellow-100 text-yellow-800',
  correction_applied: 'bg-red-100 text-red-800',
  pattern_discovered: 'bg-green-100 text-green-800',
  model_updated: 'bg-purple-100 text-purple-800',
  feedback_received: 'bg-pink-100 text-pink-800',
};

export default function LearningPage() {
  const [events, setEvents] = useState<LearningEvent[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [eventsRes, statsRes] = await Promise.all([
        learningApi.getEvents(50),
        learningApi.getStats()
      ]);
      setEvents(eventsRes.data);
      setStats(statsRes.data);
    } catch (error) { console.error(error); }
    setLoading(false);
  };

  if (loading) return <div className="min-h-screen bg-gray-50 flex items-center justify-center">加载中...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">📚 学习进度</h1>

        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total_learning_events}</div>
              <div className="text-sm text-gray-500">学习事件</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{stats.total_preferences}</div>
              <div className="text-sm text-gray-500">偏好</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.total_corrections}</div>
              <div className="text-sm text-gray-500">修正</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.total_feedbacks}</div>
              <div className="text-sm text-gray-500">反馈</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4 text-center">
              <div className="text-2xl font-bold text-pink-600">{stats.average_feedback_rating.toFixed(1)}</div>
              <div className="text-sm text-gray-500">平均评分</div>
            </div>
          </div>
        )}

        {/* 学习时间线 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">学习时间线</h2>
          {events.length === 0 ? (
            <p className="text-center py-8 text-gray-500">暂无学习事件</p>
          ) : (
            <div className="relative">
              <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200" />
              <div className="space-y-4">
                {events.map(event => (
                  <div key={event.event_id} className="relative pl-16">
                    <div className={`absolute left-6 w-5 h-5 rounded-full border-2 border-white ${EVENT_COLORS[event.event_type] || 'bg-gray-100'}`} />
                    <div className="border rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <span>{EVENT_ICONS[event.event_type] || '📌'}</span>
                        <span className="font-medium text-sm">{event.event_type}</span>
                        <span className="text-xs text-gray-400">{event.source}</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{event.content}</p>
                      <div className="text-xs text-gray-400 mt-1">
                        影响度: {(event.impact * 100).toFixed(0)}% · {new Date(event.created_at).toLocaleString('zh-CN')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
