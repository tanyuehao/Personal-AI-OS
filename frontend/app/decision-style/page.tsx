'use client';

import { useState, useEffect, useRef } from 'react';
import { decisionStyleApi } from '@/services/api';
import toast from 'react-hot-toast';

interface DecisionStyle {
  style_id: string;
  risk_tolerance: number;
  analysis_depth: number;
  decisiveness: number;
  collaboration: number;
  time_preference: number;
  evidence_reliance: number;
  intuition_ratio: number;
  emotional_influence: number;
  primary_style: string;
  secondary_style: string;
  style_description: string;
  last_analyzed_at: string | null;
}

interface Pattern {
  pattern_id: string;
  pattern_type: string;
  pattern_name: string;
  description: string;
  confidence: number;
}

const STYLE_INFO: Record<string, { name: string; icon: string; color: string; description: string; traits: string[] }> = {
  analytical: { name: '分析型', icon: '📊', color: 'blue', description: '系统性分析，数据驱动', traits: ['深度分析', '数据驱动', '系统性思考', '风险评估'] },
  intuitive: { name: '直觉型', icon: '💡', color: 'purple', description: '依赖直觉，快速决策', traits: ['快速决策', '经验驱动', '信任直觉', '模式识别'] },
  directive: { name: '指令型', icon: '🎯', color: 'red', description: '果断自信，结果导向', traits: ['果断决策', '快速执行', '自信', '结果导向'] },
  conceptual: { name: '概念型', icon: '🎨', color: 'green', description: '创新思维，长远视角', traits: ['创新思维', '长远视角', '探索性', '开放性'] },
  behavioral: { name: '行为型', icon: '🤝', color: 'yellow', description: '协作导向，人际敏感', traits: ['协作导向', '人际敏感', '团队考虑', '沟通优先'] },
  hesitant: { name: '犹豫型', icon: '🤔', color: 'gray', description: '谨慎决策，信息依赖', traits: ['信息收集', '延迟决策', '风险厌恶', '完美主义'] },
};

const DIMENSIONS = [
  { key: 'risk_tolerance', label: '风险偏好', left: '保守', right: '冒险' },
  { key: 'analysis_depth', label: '分析深度', left: '直觉', right: '深度分析' },
  { key: 'decisiveness', label: '果断程度', left: '犹豫', right: '果断' },
  { key: 'collaboration', label: '协作倾向', left: '独立', right: '协作' },
  { key: 'time_preference', label: '时间偏好', left: '短期', right: '长期' },
  { key: 'evidence_reliance', label: '证据依赖', left: '经验', right: '数据' },
  { key: 'intuition_ratio', label: '直觉比例', left: '纯分析', right: '纯直觉' },
  { key: 'emotional_influence', label: '情绪影响', left: '冷静', right: '情绪化' },
];

export default function DecisionStylePage() {
  const [style, setStyle] = useState<DecisionStyle | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [recommendationContext, setRecommendationContext] = useState('');
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (style && canvasRef.current) {
      drawRadarChart();
    }
  }, [style]);

  const loadData = async () => {
    try {
      const [styleRes, patternsRes] = await Promise.all([
        decisionStyleApi.getStyle(),
        decisionStyleApi.getPatterns()
      ]);
      setStyle(styleRes.data);
      setPatterns(patternsRes.data);
    } catch (error) {
      toast.error('加载决策风格失败');
    }
    setLoading(false);
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await decisionStyleApi.analyzeStyle();
      toast.success('分析完成');
      await loadData();
    } catch (error) {
      toast.error('分析失败');
    }
    setAnalyzing(false);
  };

  const handleRecommendation = async () => {
    if (!recommendationContext.trim()) return;
    try {
      const res = await decisionStyleApi.getRecommendations(recommendationContext);
      setRecommendations(res.data.recommendations);
    } catch (error) {
      toast.error('获取建议失败');
    }
  };

  const drawRadarChart = () => {
    const canvas = canvasRef.current;
    if (!canvas || !style) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width = canvas.offsetWidth * 2;
    const height = canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);

    const centerX = width / 4;
    const centerY = height / 4;
    const radius = Math.min(width, height) / 4 - 30;

    ctx.clearRect(0, 0, width, height);

    // 绘制背景圆圈
    for (let i = 1; i <= 5; i++) {
      ctx.beginPath();
      ctx.arc(centerX, centerY, (radius * i) / 5, 0, 2 * Math.PI);
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // 绘制轴线
    DIMENSIONS.forEach((_, i) => {
      const angle = (2 * Math.PI * i) / DIMENSIONS.length - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + radius * Math.cos(angle),
        centerY + radius * Math.sin(angle)
      );
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      ctx.stroke();
    });

    // 绘制数据点和连线
    const values = DIMENSIONS.map(d => (style as any)[d.key] || 0.5);
    ctx.beginPath();
    values.forEach((val, i) => {
      const angle = (2 * Math.PI * i) / DIMENSIONS.length - Math.PI / 2;
      const x = centerX + radius * val * Math.cos(angle);
      const y = centerY + radius * val * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 绘制数据点
    values.forEach((val, i) => {
      const angle = (2 * Math.PI * i) / DIMENSIONS.length - Math.PI / 2;
      const x = centerX + radius * val * Math.cos(angle);
      const y = centerY + radius * val * Math.sin(angle);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = '#3b82f6';
      ctx.fill();
    });

    // 绘制标签
    DIMENSIONS.forEach((dim, i) => {
      const angle = (2 * Math.PI * i) / DIMENSIONS.length - Math.PI / 2;
      const labelRadius = radius + 25;
      const x = centerX + labelRadius * Math.cos(angle);
      const y = centerY + labelRadius * Math.sin(angle);

      ctx.fillStyle = '#374151';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(dim.label, x, y);
    });
  };

  const getStyleColor = (style: string) => {
    const colors: Record<string, string> = {
      analytical: 'bg-blue-100 text-blue-800',
      intuitive: 'bg-purple-100 text-purple-800',
      directive: 'bg-red-100 text-red-800',
      conceptual: 'bg-green-100 text-green-800',
      behavioral: 'bg-yellow-100 text-yellow-800',
      hesitant: 'bg-gray-100 text-gray-800',
    };
    return colors[style] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">加载中...</div>;
  }

  const styleInfo = STYLE_INFO[style?.primary_style || 'analytical'] || STYLE_INFO.analytical;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">🧠 决策风格分析</h1>
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {analyzing ? '分析中...' : '🔄 重新分析'}
          </button>
        </div>

        {/* 主要风格 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-start gap-6">
            <div className="text-6xl">{styleInfo.icon}</div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">
                你的决策风格：{styleInfo.name}
              </h2>
              <p className="text-gray-600 mb-4">{style?.style_description}</p>
              <div className="flex gap-2 mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStyleColor(style?.primary_style || '')}`}>
                  主要：{styleInfo.name}
                </span>
                {style?.secondary_style && (
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStyleColor(style.secondary_style)}`}>
                    次要：{STYLE_INFO[style.secondary_style]?.name || style.secondary_style}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {styleInfo.traits.map((trait, i) => (
                  <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-sm">
                    {trait}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 雷达图 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">风格维度</h3>
            <canvas ref={canvasRef} className="w-full h-64" />
          </div>

          {/* 维度详情 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">维度详情</h3>
            <div className="space-y-3">
              {DIMENSIONS.map(dim => {
                const value = (style as any)?.[dim.key] || 0.5;
                return (
                  <div key={dim.key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">{dim.label}</span>
                      <span className="font-medium">{(value * 100).toFixed(0)}%</span>
                    </div>
                    <div className="relative h-2 bg-gray-200 rounded-full">
                      <div
                        className="absolute h-2 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all"
                        style={{ width: `${value * 100}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                      <span>{dim.left}</span>
                      <span>{dim.right}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* 决策模式 */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <h3 className="text-xl font-semibold mb-4">决策模式</h3>
          {patterns.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无决策模式数据</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {patterns.map(pattern => (
                <div key={pattern.pattern_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <h4 className="font-medium">{pattern.pattern_name}</h4>
                    <span className="text-sm text-gray-500">
                      置信度: {(pattern.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-gray-600 text-sm mt-1">{pattern.description}</p>
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full"
                        style={{ width: `${pattern.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 决策建议 */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <h3 className="text-xl font-semibold mb-4">💡 个性化决策建议</h3>
          <div className="flex gap-4 mb-4">
            <input
              type="text"
              value={recommendationContext}
              onChange={e => setRecommendationContext(e.target.value)}
              placeholder="描述你的决策场景..."
              className="flex-1 border rounded-lg px-4 py-2"
              onKeyDown={e => e.key === 'Enter' && handleRecommendation()}
            />
            <button
              onClick={handleRecommendation}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
            >
              获取建议
            </button>
          </div>
          {recommendations.length > 0 && (
            <div className="space-y-3">
              {recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="text-blue-600 font-bold">{i + 1}.</span>
                  <p className="text-gray-700">{rec}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
