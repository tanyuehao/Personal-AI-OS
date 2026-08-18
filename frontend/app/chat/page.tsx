'use client';

import { useState, useEffect, useRef } from 'react';
import { aiApi } from '@/services/api';
import toast from 'react-hot-toast';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    document_name: string;
    content: string;
    relevance_score?: number;
  }>;
}

interface Conversation {
  conversation_id: string;
  title: string;
  updated_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const response = await aiApi.listConversations();
      setConversations(response.data);
    } catch (error) {
      toast.error('加载对话列表失败');
    }
  };

  const loadConversation = async (conversationId: string) => {
    try {
      const response = await aiApi.getConversationMessages(conversationId);
      const msgs = response.data.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        sources: msg.sources
      }));
      setMessages(msgs);
      setCurrentConversationId(conversationId);
    } catch (error) {
      toast.error('加载对话失败');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await aiApi.chat({
        message: userMessage.content,
        conversation_id: currentConversationId || undefined,
        memory_enabled: true
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
      setCurrentConversationId(response.data.conversation_id);
      
      // 刷新对话列表
      await loadConversations();
    } catch (error) {
      toast.error('发送消息失败');
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，发生了错误。请稍后重试。'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* 侧边栏 - 对话列表 */}
      <div className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-lg">💬 对话列表</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <p className="p-4 text-gray-500 text-sm">暂无对话</p>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.conversation_id}
                className={`p-3 border-b cursor-pointer hover:bg-gray-50 group ${
                  currentConversationId === conv.conversation_id ? 'bg-blue-50' : ''
                }`}
                onClick={() => loadConversation(conv.conversation_id)}
              >
                <div className="flex justify-between items-start">
                  <p className="font-medium text-sm truncate flex-1">{conv.title}</p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('确定删除这个对话吗？')) {
                        aiApi.deleteConversation(conv.conversation_id).then(() => {
                          setConversations(conversations.filter(c => c.conversation_id !== conv.conversation_id));
                          if (currentConversationId === conv.conversation_id) {
                            setCurrentConversationId(null);
                            setMessages([]);
                          }
                        });
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 ml-2 text-xs"
                  >
                    删除
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(conv.updated_at).toLocaleString('zh-CN')}
                </p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-700 mb-2">🧠 Personal AI OS</h3>
                <p className="text-gray-500">开始提问，让 AI 帮你理解知识</p>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white shadow-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  
                  {/* 引用来源 */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-sm font-medium text-gray-600 mb-2">📚 引用来源：</p>
                      {msg.sources.map((source, i) => (
                        <div
                          key={i}
                          className="text-xs bg-gray-100 rounded p-2 mb-1"
                        >
                          <p className="font-medium">{source.document_name}</p>
                          <p className="text-gray-600 line-clamp-2">{source.content}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-lg p-4 shadow-md">
                <p className="text-gray-500">正在思考...</p>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="border-t bg-white p-4">
          <div className="max-w-4xl mx-auto flex gap-4">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="输入你的问题..."
              className="flex-1 border rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
