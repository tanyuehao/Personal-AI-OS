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
      console.error('加载对话列表失败');
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
    <div className="flex h-screen bg-gray-50">
      {/* 侧边栏 - 对话列表 */}
      <div className="w-72 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <button
            onClick={() => {
              setMessages([]);
              setCurrentConversationId(null);
            }}
            className="w-full btn btn-primary"
          >
            + 新对话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {conversations.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">暂无对话</p>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.conversation_id}
                className={`p-3 rounded-lg cursor-pointer transition-all duration-200 mb-1 ${
                  currentConversationId === conv.conversation_id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => {
                  setCurrentConversationId(conv.conversation_id);
                  // 加载对话历史
                }}
              >
                <p className="font-medium text-sm truncate">{conv.title || '新对话'}</p>
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
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center animate-fade-in">
                <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-4xl">🧠</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-700 mb-2">Personal AI OS</h3>
                <p className="text-gray-500">开始提问，让 AI 帮你理解知识</p>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
              >
                <div
                  className={`max-w-3xl rounded-2xl p-4 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white shadow-md border border-gray-100'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  
                  {/* 引用来源 */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-sm font-medium text-gray-600 mb-2">📚 引用来源：</p>
                      {msg.sources.map((source, i) => (
                        <div
                          key={i}
                          className="text-xs bg-gray-100 rounded-lg p-2 mb-1"
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
            <div className="flex justify-start animate-fade-in">
              <div className="bg-white rounded-2xl p-4 shadow-md border border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="border-t bg-white p-4">
          <div className="max-w-4xl mx-auto flex gap-3">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入你的问题..."
              className="flex-1 input resize-none"
              rows={2}
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="btn btn-primary px-6"
            >
              {isLoading ? '发送中...' : '发送'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
