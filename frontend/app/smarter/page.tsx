'use client';

import { useState } from 'react';
import { smarterApi } from '@/services/api';
import toast from 'react-hot-toast';

interface BlindSpot {
  area: string;
  description: string;
  impact: string;
  suggestion: string;
  confidence: number;
}

interface CounterArgument {
  original_claim: string;
  counter_claim: string;
  evidence: string[];
  strength: number;
  recommendation: string;
}

interface CrossDomainInsight {
  domain_a: string;
  domain_b: string;
  connection: string;
  insight: string;
  value: string;
}

interface BestPractice {
  area: string;
  practice: string;
  description: string;
  source: string;
  applicability: number;
}

interface DecisionOptimization {
  original_decision: string;
  alternative: string;
  reasoning: string;
  expected_improvement: string;
  confidence: number;
}

type Tab = 'blind-spots' | 'counter-arguments' | 'cross-domain' | 'best-practices' | 'optimize';

export default function SmarterPage() {
  const [activeTab, setActiveTab] = useState<Tab>('blind-spots');
  const [loading, setLoading] = useState<string | null>(null);

  // 盲区
  const [blindSpots, setBlindSpots] = useState<BlindSpot[]>([]);

  // 反面论证
  const [claim, setClaim] = useState('');
  const [counterArgs, setCounterArgs] = useState<CounterArgument[]>([]);

  // 跨领域
  const [crossDomain, setCrossDomain] = useState<CrossDomainInsight[]>([]);

  // 最佳实践
  const [bestPractices, setBestPractices] = useState<BestPractice[]>([]);

  // 决策优化
  const [decisionProblem, setDecisionProblem] = useState('');
  const [currentChoice, setCurrentChoice] = useState('');
  const [optimizations, setOptimizations] = useState<DecisionOptimization[]>([]);

  const loadBlindSpots = async () => {
    setLoading('blind-spots');
    try {
      const res = await smarterApi.findBlindSpots();
      setBlindSpots(res.data);
      toast.success(`发现 ${res.data.length} 个盲区`);
    } catch (error) { toast.error('分析失败'); }
    setLoading(null);
  };

  const loadCounterArguments = async () => {
    if (!claim.trim()) { toast.error('请输入观点'); return; }
    setLoading('counter-arguments');
    try {
      const res = await smarterApi.counterArguments(claim);
      setCounterArgs(res.data);
      toast.success(`生成 ${res.data.length} 个反面论据`);
    } catch (error) { toast.error('分析失败'); }
    setLoading(null);
  };

  const loadCrossDomain = async () => {
    setLoading('cross-domain');
    try {
      const res = await smarterApi.crossDomain();
      setCrossDomain(res.data);
      toast.success(`发现 ${res.data.length} 个跨领域洞察`);
    } catch (error) { toast.error('分析失败'); }
    setLoading(null);
  };

  const loadBestPractices = async () => {
    setLoading('best-practices');
    try {
      const res = await smarterApi.bestPractices();
      setBestPractices(res.data);
      toast.success(`推荐 ${res.data.length} 个最佳实践`);
    } catch (error) { toast.error('分析失败'); }
    setLoading(null);
  };

  const loadOptimizations = async () => {
    if (!decisionProblem.trim()) { toast.error('请输入决策问题'); return; }
    setLoading('optimize');
    try {
      const res = await smarterApi.optimizeDecision(decisionProblem, currentChoice);
      setOptimizations(res.data);
      toast.success(`生成 ${res.data.length} 个优化建议`);
    } catch (error) { toast.error('分析失败'); }
    setLoading(null);
  };

  const tabs = [
    { key: 'blind-spots' as Tab, label: '🔍 盲区发现', count: blindSpots.length },
    { key: 'counter-arguments' as Tab, label: '⚖️ 反面论证', count: counterArgs.length },
    { key: 'cross-domain' as Tab, label: '🔗 跨领域洞察', count: crossDomain.length },
    { key: 'best-practices' as Tab, label: '🏆 最佳实践', count: bestPractices.length },
    { key: 'optimize' as Tab, label: '🎯 决策优化', count: optimizations.length },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">🧠 比你更聪明</h1>
          <p className="text-gray-500 mt-1">发现盲区、挑战假设、跨领域综合、推荐最佳实践</p>
        </div>

        {/* 标签页 */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* 盲区发现 */}
        {activeTab === 'blind-spots' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">🔍 思维盲区发现</h2>
              <button
                onClick={loadBlindSpots}
                disabled={loading === 'blind-spots'}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading === 'blind-spots' ? '分析中...' : '🔄 分析盲区'}
              </button>
            </div>
            <p className="text-gray-600 mb-4">找出你可能忽视的角度和思维盲点</p>

            {blindSpots.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">🔍</div>
                <p>点击"分析盲区"开始</p>
              </div>
            ) : (
              <div className="space-y-4">
                {blindSpots.map((spot, i) => (
                  <div key={i} className="border rounded-lg p-4 hover:shadow-md transition">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-sm font-medium">
                          {spot.area}
                        </span>
                        <h3 className="font-medium mt-2">{spot.description}</h3>
                      </div>
                      <span className="text-sm text-gray-500">
                        置信度: {(spot.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-4">
                      <div className="bg-red-50 rounded p-3">
                        <div className="text-xs text-red-600 font-medium">⚠️ 影响</div>
                        <div className="text-sm text-red-700">{spot.impact}</div>
                      </div>
                      <div className="bg-green-50 rounded p-3">
                        <div className="text-xs text-green-600 font-medium">💡 建议</div>
                        <div className="text-sm text-green-700">{spot.suggestion}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 反面论证 */}
        {activeTab === 'counter-arguments' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">⚖️ 反面论证</h2>
            <p className="text-gray-600 mb-4">对你的观点提出质疑，帮助全面思考</p>

            <div className="flex gap-4 mb-6">
              <input
                type="text"
                value={claim}
                onChange={e => setClaim(e.target.value)}
                placeholder="输入你要论证的观点..."
                className="flex-1 border rounded-lg px-4 py-2"
                onKeyDown={e => e.key === 'Enter' && loadCounterArguments()}
              />
              <button
                onClick={loadCounterArguments}
                disabled={loading === 'counter-arguments'}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading === 'counter-arguments' ? '分析中...' : '🔄 生成反面论据'}
              </button>
            </div>

            {counterArgs.length > 0 && (
              <div className="space-y-4">
                {counterArgs.map((arg, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-red-700">反面观点 {i + 1}</h3>
                      <span className="text-sm text-gray-500">
                        强度: {(arg.strength * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-gray-800 mb-3">{arg.counter_claim}</p>
                    <div className="mb-3">
                      <div className="text-xs text-gray-500 mb-1">支持证据：</div>
                      {arg.evidence.map((e, j) => (
                        <div key={j} className="text-sm text-gray-600 ml-2">• {e}</div>
                      ))}
                    </div>
                    <div className="bg-blue-50 rounded p-3">
                      <div className="text-xs text-blue-600 font-medium">💡 建议</div>
                      <div className="text-sm text-blue-700">{arg.recommendation}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 跨领域洞察 */}
        {activeTab === 'cross-domain' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">🔗 跨领域洞察</h2>
              <button
                onClick={loadCrossDomain}
                disabled={loading === 'cross-domain'}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading === 'cross-domain' ? '分析中...' : '🔄 发现洞察'}
              </button>
            </div>
            <p className="text-gray-600 mb-4">连接不同领域的知识，发现新的联系</p>

            {crossDomain.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">🔗</div>
                <p>点击"发现洞察"开始</p>
              </div>
            ) : (
              <div className="space-y-4">
                {crossDomain.map((insight, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                        {insight.domain_a}
                      </span>
                      <span className="text-gray-400">↔</span>
                      <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                        {insight.domain_b}
                      </span>
                    </div>
                    <div className="mb-2">
                      <div className="text-xs text-gray-500">联系</div>
                      <div className="text-sm text-gray-700">{insight.connection}</div>
                    </div>
                    <div className="mb-2">
                      <div className="text-xs text-gray-500">洞察</div>
                      <div className="text-sm font-medium text-gray-800">{insight.insight}</div>
                    </div>
                    <div className="bg-green-50 rounded p-2">
                      <div className="text-xs text-green-600">价值</div>
                      <div className="text-sm text-green-700">{insight.value}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 最佳实践 */}
        {activeTab === 'best-practices' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">🏆 最佳实践</h2>
              <button
                onClick={loadBestPractices}
                disabled={loading === 'best-practices'}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading === 'best-practices' ? '分析中...' : '🔄 推荐实践'}
              </button>
            </div>
            <p className="text-gray-600 mb-4">基于你的情况，推荐行业最佳实践</p>

            {bestPractices.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">🏆</div>
                <p>点击"推荐实践"开始</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {bestPractices.map((practice, i) => (
                  <div key={i} className="border rounded-lg p-4 hover:shadow-md transition">
                    <div className="flex items-start justify-between mb-2">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                        {practice.area}
                      </span>
                      <span className="text-sm text-gray-500">
                        适用度: {(practice.applicability * 100).toFixed(0)}%
                      </span>
                    </div>
                    <h3 className="font-medium mb-2">{practice.practice}</h3>
                    <p className="text-sm text-gray-600 mb-2">{practice.description}</p>
                    <div className="text-xs text-gray-400">来源: {practice.source}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 决策优化 */}
        {activeTab === 'optimize' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">🎯 决策优化</h2>
            <p className="text-gray-600 mb-4">分析你的决策，给出更好的替代方案</p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">决策问题</label>
                <input
                  type="text"
                  value={decisionProblem}
                  onChange={e => setDecisionProblem(e.target.value)}
                  placeholder="你面临的决策问题..."
                  className="w-full border rounded-lg px-4 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">当前选择（可选）</label>
                <input
                  type="text"
                  value={currentChoice}
                  onChange={e => setCurrentChoice(e.target.value)}
                  placeholder="你目前倾向的选择..."
                  className="w-full border rounded-lg px-4 py-2"
                />
              </div>
              <button
                onClick={loadOptimizations}
                disabled={loading === 'optimize'}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading === 'optimize' ? '分析中...' : '🔄 优化决策'}
              </button>
            </div>

            {optimizations.length > 0 && (
              <div className="space-y-4">
                {optimizations.map((opt, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium">替代方案 {i + 1}</h3>
                      <span className="text-sm text-gray-500">
                        置信度: {(opt.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-gray-800 mb-3">{opt.alternative}</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-blue-50 rounded p-3">
                        <div className="text-xs text-blue-600 font-medium">💡 理由</div>
                        <div className="text-sm text-blue-700">{opt.reasoning}</div>
                      </div>
                      <div className="bg-green-50 rounded p-3">
                        <div className="text-xs text-green-600 font-medium">📈 预期改进</div>
                        <div className="text-sm text-green-700">{opt.expected_improvement}</div>
                      </div>
                    </div>
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
