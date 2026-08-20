'use client';

export default function HelpPage() {
  const shortcuts = [
    { keys: 'Ctrl + K', action: '打开 AI 聊天' },
    { keys: 'Ctrl + B', action: '打开知识库' },
    { keys: 'Ctrl + M', action: '打开记忆' },
    { keys: 'Ctrl + D', action: '打开控制面板' },
    { keys: 'Ctrl + G', action: '打开知识图谱' },
    { keys: 'Ctrl + P', action: '打开主动智能' },
    { keys: 'Ctrl + ,', action: '打开设置' },
    { keys: '/', action: '聚焦聊天输入' },
  ];

  const features = [
    { icon: '📚', name: '知识库', description: '上传文档，自动解析、切片、向量化，支持语义搜索' },
    { icon: '💬', name: 'AI 聊天', description: '基于知识库的 RAG 问答，支持记忆集成' },
    { icon: '🧠', name: '记忆系统', description: '长期记忆管理，支持候选确认机制' },
    { icon: '🔗', name: '知识图谱', description: '可视化知识关联关系' },
    { icon: '🎯', name: '决策中心', description: '记录决策，分析决策风格' },
    { icon: '🧬', name: '决策风格', description: '8 维决策风格分析' },
    { icon: '🔮', name: '主动智能', description: 'AI 主动发现信息和建议' },
    { icon: '📈', name: '学习进度', description: '追踪学习事件和偏好' },
    { icon: '🤖', name: 'Agent', description: '专业智能助手' },
    { icon: '📷', name: '多模态', description: '图片识别和语音转写' },
    { icon: '⚙️', name: '设置', description: 'AI 提供商配置、数据导出' },
    { icon: '📊', name: '使用量', description: 'API 使用统计' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">❓ 帮助中心</h1>

        {/* 快捷键 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">⌨️ 键盘快捷键</h2>
          <div className="grid grid-cols-2 gap-4">
            {shortcuts.map((s, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <kbd className="px-2 py-1 bg-gray-200 rounded text-sm font-mono">{s.keys}</kbd>
                <span className="text-sm text-gray-600">{s.action}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 功能说明 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🚀 功能说明</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {features.map((f, i) => (
              <div key={i} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                <div className="text-2xl mb-2">{f.icon}</div>
                <h3 className="font-medium">{f.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{f.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* AI 使用提示 */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">💡 使用提示</h2>
          <div className="space-y-3">
            <div className="p-3 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-800">让 AI 记住你</h3>
              <p className="text-sm text-blue-600">在对话中告诉 AI 你的偏好、经验和观点，它会自动记住。</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <h3 className="font-medium text-green-800">上传你的资料</h3>
              <p className="text-sm text-green-600">上传项目文档、笔记、报告，AI 会基于这些资料回答问题。</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <h3 className="font-medium text-purple-800">纠正 AI</h3>
              <p className="text-sm text-purple-600">当 AI 说错时，纠正它，系统会学习并改进。</p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg">
              <h3 className="font-medium text-yellow-800">查看主动智能</h3>
              <p className="text-sm text-yellow-600">AI 会主动发现信息、预测需求、提供建议。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
