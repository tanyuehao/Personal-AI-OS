'use client';

import { useState, useEffect } from 'react';
import { usageApi } from '@/services/api';

interface UsageStats {
  total_requests: number;
  total_tokens: number;
  current_rpm: number;
  current_tpm: number;
  rpm_limit: number;
  tpm_limit: number;
  rpm_remaining: number;
  tpm_remaining: number;
  rpm_usage_percent: number;
  tpm_usage_percent: number;
}

export default function UsagePage() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
    // 暂时移除自动刷新，避免持续消耗 token
    // const interval = setInterval(loadStats, 5000);
    // return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const response = await usageApi.getStats();
      setStats(response.data);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  if (loading) return <div className="p-8">加载中...</div>;
  if (!stats) return <div className="p-8">加载失败</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">使用量统计</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* RPM 统计 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">请求频率 (RPM)</h2>
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span>当前使用</span>
                <span>{stats.current_rpm} / {stats.rpm_limit}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${stats.rpm_usage_percent > 80 ? 'bg-red-500' : stats.rpm_usage_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(stats.rpm_usage_percent, 100)}%` }}
                />
              </div>
            </div>
            <div className="text-sm text-gray-500">
              剩余: {stats.rpm_remaining} 次/分钟
            </div>
          </div>

          {/* TPM 统计 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Token 使用量 (TPM)</h2>
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span>当前使用</span>
                <span>{stats.current_tpm.toLocaleString()} / {stats.tpm_limit.toLocaleString()}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${stats.tpm_usage_percent > 80 ? 'bg-red-500' : stats.tpm_usage_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(stats.tpm_usage_percent, 100)}%` }}
                />
              </div>
            </div>
            <div className="text-sm text-gray-500">
              剩余: {stats.tpm_remaining.toLocaleString()} tokens/分钟
            </div>
          </div>

          {/* 总量统计 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">累计使用</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">总请求数</span>
                <span className="font-semibold">{stats.total_requests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">总 Token 数</span>
                <span className="font-semibold">{stats.total_tokens.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* 限制说明 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">API 限制说明</h2>
            <div className="space-y-2 text-sm text-gray-600">
              <p>• RPM (Requests Per Minute): 每分钟请求数限制</p>
              <p>• TPM (Tokens Per Minute): 每分钟 Token 数限制</p>
              <p>• 突发限制: 1秒内最大并发请求数</p>
              <p className="mt-4 text-blue-600">
                当前配置: {stats.rpm_limit} RPM / {stats.tpm_limit.toLocaleString()} TPM
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
