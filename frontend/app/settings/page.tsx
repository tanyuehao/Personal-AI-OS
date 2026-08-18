'use client';

import { useState, useEffect, useRef } from 'react';
import { settingsApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Model { id: string; name: string; }
interface Models { chat: Model[]; embedding: Model[]; rerank: Model[]; image: Model[]; }
interface UserSettings {
  settings_id: string; ai_provider: string; siliconflow_api_key: string;
  siliconflow_api_base: string; deepseek_api_key: string; deepseek_api_base: string;
  llm_model: string; embedding_model: string; reranker_enabled: boolean;
  reranker_model: string; image_model_enabled: boolean; image_model: string;
  temperature: string; max_tokens: string;
}

function ModelSelect({ models, value, onChange, placeholder }: { models: Model[]; value: string; onChange: (val: string) => void; placeholder: string; }) {
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [filteredModels, setFilteredModels] = useState<Model[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFilteredModels(search ? models.filter(m => m.id.toLowerCase().includes(search.toLowerCase()) || m.name.toLowerCase().includes(search.toLowerCase())) : models);
  }, [search, models]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => { if (containerRef.current && !containerRef.current.contains(e.target as Node)) setIsOpen(false); };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedModel = models.find(m => m.id === value);

  return (
    <div ref={containerRef} className="relative">
      <div className="w-full border rounded-lg p-2 cursor-pointer bg-white flex items-center justify-between" onClick={() => { setIsOpen(!isOpen); inputRef.current?.focus(); }}>
        <span className={selectedModel ? 'text-gray-800' : 'text-gray-400'}>{selectedModel ? selectedModel.name || selectedModel.id : placeholder}</span>
        <span className="text-gray-400">{isOpen ? '▲' : '▼'}</span>
      </div>
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-auto">
          <div className="p-2 border-b"><input ref={inputRef} type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索模型..." className="w-full border rounded px-2 py-1 text-sm" onClick={e => e.stopPropagation()} /></div>
          <div className="max-h-48 overflow-auto">
            {filteredModels.length === 0 ? <div className="p-2 text-gray-500 text-sm">未找到匹配的模型</div> : filteredModels.map(model => (
              <div key={model.id} className={`p-2 cursor-pointer hover:bg-gray-100 ${model.id === value ? 'bg-blue-100' : ''}`} onClick={() => { onChange(model.id); setSearch(''); setIsOpen(false); }}>
                <div className="text-sm font-medium">{model.name || model.id}</div>
                <div className="text-xs text-gray-500">{model.id}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {value && <div className="mt-1 text-xs text-gray-500 truncate">当前: {value}</div>}
    </div>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [models, setModels] = useState<Models | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [activeProvider, setActiveProvider] = useState<'siliconflow' | 'deepseek'>('siliconflow');

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    try {
      const r = await settingsApi.get();
      setSettings(r.data);
      if (r.data.ai_provider === 'deepseek') setActiveProvider('deepseek');
      const apiKey = r.data.ai_provider === 'deepseek' ? r.data.deepseek_api_key : r.data.siliconflow_api_key;
      if (apiKey && !apiKey.includes('****')) loadModels(apiKey);
    } catch (e) { toast.error('加载设置失败'); }
  };

  const loadModels = async (apiKey: string) => {
    setIsLoadingModels(true);
    try {
      const r = await settingsApi.getModels(apiKey);
      setModels(r.data);
    } catch (e) { toast.error('加载模型列表失败'); }
    setIsLoadingModels(false);
  };

  const handleSave = async () => {
    if (!settings) return;
    setIsSaving(true);
    try {
      await settingsApi.update({ ...settings, ai_provider: activeProvider });
      toast.success('保存成功！');
    } catch (e) { toast.error('保存失败'); }
    setIsSaving(false);
  };

  const handleApiKeyChange = (key: string) => {
    if (!settings) return;
    if (activeProvider === 'siliconflow') {
      setSettings({ ...settings, siliconflow_api_key: key });
    } else {
      setSettings({ ...settings, deepseek_api_key: key });
    }
    if (key.length > 10 && !key.includes('****')) loadModels(key);
  };

  const handleProviderSwitch = (provider: 'siliconflow' | 'deepseek') => {
    setActiveProvider(provider);
    if (settings) {
      setSettings({ ...settings, ai_provider: provider });
      const apiKey = provider === 'deepseek' ? settings.deepseek_api_key : settings.siliconflow_api_key;
      if (apiKey && !apiKey.includes('****')) loadModels(apiKey);
      else setModels(null);
    }
  };

  if (!settings) return <div className="p-8">加载中...</div>;

  const currentApiKey = activeProvider === 'siliconflow' ? settings.siliconflow_api_key : settings.deepseek_api_key;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">⚙️ 设置</h1>

        {/* 提供商选择 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">AI 提供商</h2>
          <div className="flex gap-4">
            <button
              onClick={() => handleProviderSwitch('siliconflow')}
              className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                activeProvider === 'siliconflow'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-medium">SiliconFlow</div>
              <div className="text-sm text-gray-500 mt-1">推荐 · 有免费额度</div>
            </button>
            <button
              onClick={() => handleProviderSwitch('deepseek')}
              className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                activeProvider === 'deepseek'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-medium">DeepSeek</div>
              <div className="text-sm text-gray-500 mt-1">更便宜 · 直连</div>
            </button>
          </div>
        </div>

        {/* API Key */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">
            {activeProvider === 'siliconflow' ? 'SiliconFlow' : 'DeepSeek'} API Key
          </h2>
          <div className="flex gap-2">
            <input
              type={showKeys.current ? 'text' : 'password'}
              value={currentApiKey}
              onChange={e => handleApiKeyChange(e.target.value)}
              className="flex-1 border rounded-lg p-2"
              placeholder="sk-..."
            />
            <button
              onClick={() => setShowKeys({...showKeys, current: !showKeys.current})}
              className="px-3 py-2 border rounded-lg"
            >
              {showKeys.current ? '🙈' : '👁️'}
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            注册地址:{' '}
            <a
              href={activeProvider === 'siliconflow' ? 'https://siliconflow.cn/' : 'https://platform.deepseek.com/'}
              target="_blank"
              className="text-blue-600"
            >
              {activeProvider === 'siliconflow' ? 'https://siliconflow.cn/' : 'https://platform.deepseek.com/'}
            </a>
          </p>
        </div>

        {/* 模型配置 */}
        {isLoadingModels && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6 text-center text-gray-500">
            正在加载模型列表...
          </div>
        )}
        {models && (
          <>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">语言模型</h2>
              <ModelSelect
                models={models.chat}
                value={settings.llm_model}
                onChange={val => setSettings({...settings, llm_model: val})}
                placeholder="选择语言模型"
              />
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">Embedding 模型</h2>
              <ModelSelect
                models={models.embedding}
                value={settings.embedding_model}
                onChange={val => setSettings({...settings, embedding_model: val})}
                placeholder="选择 Embedding 模型"
              />
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">Reranker</h2>
              <label className="flex items-center mb-2">
                <input
                  type="checkbox"
                  checked={settings.reranker_enabled}
                  onChange={e => setSettings({...settings, reranker_enabled: e.target.checked})}
                  className="mr-2"
                />
                启用 Reranker
              </label>
              {settings.reranker_enabled && (
                <ModelSelect
                  models={models.rerank}
                  value={settings.reranker_model}
                  onChange={val => setSettings({...settings, reranker_model: val})}
                  placeholder="选择 Reranker 模型"
                />
              )}
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">图片模型</h2>
              <label className="flex items-center mb-2">
                <input
                  type="checkbox"
                  checked={settings.image_model_enabled}
                  onChange={e => setSettings({...settings, image_model_enabled: e.target.checked})}
                  className="mr-2"
                />
                启用图片生成
              </label>
              {settings.image_model_enabled && (
                <ModelSelect
                  models={models.image}
                  value={settings.image_model}
                  onChange={val => setSettings({...settings, image_model: val})}
                  placeholder="选择图片模型"
                />
              )}
            </div>
          </>
        )}

        {/* 高级设置 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">高级设置</h2>

          {/* Temperature */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <label className="font-medium">Temperature（温度）</label>
              <span className="text-sm text-gray-500">{settings.temperature || '0.7'}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature || '0.7'}
              onChange={e => setSettings({...settings, temperature: e.target.value})}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>0 - 更精确</span>
              <span>1 - 均衡</span>
              <span>2 - 更随机</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div>
            <label className="font-medium block mb-2">Max Tokens（最大 Token 数）</label>
            <input
              type="number"
              min="100"
              max="16000"
              step="100"
              value={settings.max_tokens || '2000'}
              onChange={e => setSettings({...settings, max_tokens: e.target.value})}
              className="w-full border rounded-lg p-2"
              placeholder="2000"
            />
            <p className="text-xs text-gray-400 mt-1">控制 AI 回复的最大长度，推荐 2000-4000</p>
          </div>
        </div>

        {/* 保存按钮 */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isSaving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
}
