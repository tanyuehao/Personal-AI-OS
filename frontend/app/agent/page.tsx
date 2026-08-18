'use client';

import { useState, useEffect } from 'react';
import { agentApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Agent {
  type: string;
  name: string;
  description: string;
  icon: string;
}

interface AgentTask {
  task_id: string;
  agent_type: string;
  title?: string;
  input_text: string;
  status: string;
  result?: string;
  created_at: string;
}

export default function AgentPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentResult, setCurrentResult] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
    loadTasks();
  }, []);

  const loadAgents = async () => {
    try {
      const response = await agentApi.list();
      setAgents(response.data.agents);
    } catch (error) {
      toast.error('加载 Agent 失败');
    }
  };

  const loadTasks = async () => {
    try {
      const response = await agentApi.listTasks();
      setTasks(response.data.items);
    } catch (error) {
      toast.error('加载任务失败');
    }
  };

  const handleRun = async () => {
    if (!selectedAgent || !input.trim()) return;

    setIsRunning(true);
    setCurrentResult(null);

    try {
      const response = await agentApi.run({
        agent_type: selectedAgent.type,
        input: input,
        title: input.substring(0, 50)
      });

      setCurrentResult(response.data.result);
      await loadTasks();
    } catch (error) {
      toast.error('Agent 执行失败');
      setCurrentResult('执行失败，请重试');
    }

    setIsRunning(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Agent 工作台</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：Agent 列表 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-semibold mb-4">选择 Agent</h2>
              <div className="space-y-2">
                {agents.map(agent => (
                  <button
                    key={agent.type}
                    onClick={() => setSelectedAgent(agent)}
                    className={`w-full p-4 rounded-lg text-left transition ${
                      selectedAgent?.type === agent.type
                        ? 'bg-blue-100 border-2 border-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{agent.icon}</span>
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-gray-500">{agent.description}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 中间：输入和结果 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              {selectedAgent ? (
                <>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-3xl">{selectedAgent.icon}</span>
                    <div>
                      <h2 className="text-xl font-semibold">{selectedAgent.name}</h2>
                      <p className="text-gray-500">{selectedAgent.description}</p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      输入内容
                    </label>
                    <textarea
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      className="w-full border rounded-lg p-3 h-32 resize-none focus:ring-2 focus:ring-blue-500"
                      placeholder={`请输入需要${selectedAgent.name}的内容...`}
                    />
                  </div>

                  <button
                    onClick={handleRun}
                    disabled={isRunning || !input.trim()}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isRunning ? '执行中...' : '开始分析'}
                  </button>

                  {currentResult && (
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                      <h3 className="font-medium mb-2">分析结果：</h3>
                      <div className="whitespace-pre-wrap text-gray-700">{currentResult}</div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center text-gray-500 py-12">
                  请先选择一个 Agent
                </div>
              )}
            </div>

            {/* 历史任务 */}
            <div className="bg-white rounded-lg shadow-md p-6 mt-6">
              <h2 className="text-lg font-semibold mb-4">历史任务</h2>
              {tasks.length === 0 ? (
                <p className="text-gray-500 text-center py-4">暂无历史任务</p>
              ) : (
                <div className="space-y-3">
                  {tasks.slice(0, 5).map(task => (
                    <div
                      key={task.task_id}
                      className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                      onClick={() => {
                        const agent = agents.find(a => a.type === task.agent_type);
                        if (agent) setSelectedAgent(agent);
                        setInput(task.input_text);
                        setCurrentResult(task.result || null);
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-medium">{task.agent_type}</span>
                          <p className="text-sm text-gray-600 mt-1">{task.input_text.substring(0, 100)}...</p>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded ${
                          task.status === 'completed' ? 'bg-green-100 text-green-800' :
                          task.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {task.status === 'completed' ? '完成' : task.status === 'failed' ? '失败' : '运行中'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
