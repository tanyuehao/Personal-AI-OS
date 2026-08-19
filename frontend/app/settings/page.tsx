'use client';

import { useState, useEffect } from 'react';
import { settingsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface UserSettings {
  settings_id: string; ai_provider: string; siliconflow_api_key: string;
  siliconflow_api_base: string; deepseek_api_key: string; deepseek_api_base: string;
  llm_model: string; embedding_model: string; reranker_enabled: boolean;
  reranker_model: string; image_model_enabled: boolean; image_model: string;
  temperature: string; max_tokens: string;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    try {
      const r = await settingsApi.get();
      setSettings(r.data);
    } catch (e) { toast.error('加载设置失败'); }
  };

  const handleSave = async () => {
    if (!settings) return;
    setIsSaving(true);
    try { await settingsApi.update(settings); toast.success('保存成功！'); } catch (e) { toast.error('保存失败'); }
    setIsSaving(false);
  };

  if (!settings) return <div className="p-8">加载中...</div>;

  return (
    <div className="p-8 animate-fade-in">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">⚙️ 设置</h1>
        
        <div className="card mb-6">
          <h2 className="card-header">API Key</h2>
          <div>
            <label className="label">硅基流动 API Key</label>
            <input type="password" value={settings.siliconflow_api_key} onChange={e => setSettings({...settings, siliconflow_api_key: e.target.value})} className="input" placeholder="sk-..." />
          </div>
          <p className="text-sm text-gray-500 mt-2">注册地址: <a href="https://siliconflow.cn/" target="_blank" className="text-blue-600">https://siliconflow.cn/</a></p>
        </div>

        <div className="card mb-6">
          <h2 className="card-header">模型配置</h2>
          <div className="space-y-4">
            <div>
              <label className="label">语言模型</label>
              <input type="text" value={settings.llm_model} onChange={e => setSettings({...settings, llm_model: e.target.value})} className="input" />
            </div>
            <div>
              <label className="label">Embedding 模型</label>
              <input type="text" value={settings.embedding_model} onChange={e => setSettings({...settings, embedding_model: e.target.value})} className="input" />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={handleSave} disabled={isSaving} className="btn btn-primary px-8">
            {isSaving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
}
