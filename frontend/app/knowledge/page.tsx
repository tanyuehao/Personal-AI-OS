'use client';

import { useState, useEffect } from 'react';
import { documentApi } from '@/services/api';

interface Document {
  document_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  status: string;
  summary?: string;
  created_at: string;
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await documentApi.list();
      setDocuments(response.data.items);
    } catch (error) {
      console.error('加载文档失败:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', '默认分类');

      await documentApi.upload(formData);
      
      // 刷新文档列表
      await loadDocuments();
      
      alert('上传成功！');
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败，请重试');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('确定要删除这个文档吗？')) return;

    try {
      await documentApi.delete(documentId);
      await loadDocuments();
      alert('删除成功！');
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败，请重试');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'PROCESSING':
        return 'bg-yellow-100 text-yellow-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'UPLOADING':
        return '上传中';
      case 'PROCESSING':
        return '处理中';
      case 'COMPLETED':
        return '已完成';
      case 'FAILED':
        return '失败';
      default:
        return status;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">📚 知识库管理</h1>

        {/* 上传区域 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">上传文档</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.doc,.docx,.md,.txt,.csv,.xlsx,.xls"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer text-blue-600 hover:text-blue-800"
            >
              {isUploading ? (
                <span>正在上传...</span>
              ) : (
                <span>点击或拖拽文件到此处上传</span>
              )}
            </label>
            <p className="text-gray-500 mt-2">
              支持格式：PDF, Word, Markdown, TXT, CSV, Excel
            </p>
            <p className="text-gray-500">最大文件大小：50MB</p>
          </div>
        </div>

        {/* 文档列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">文档列表</h2>
          
          {documents.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              还没有上传任何文档，点击上方上传按钮开始
            </p>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-lg">{doc.file_name}</h3>
                      <p className="text-gray-500 text-sm mt-1">
                        {doc.file_type.toUpperCase()} • {(doc.file_size / 1024).toFixed(1)} KB
                      </p>
                      {doc.summary && (
                        <p className="text-gray-600 mt-2 line-clamp-2">
                          {doc.summary}
                        </p>
                      )}
                      <p className="text-gray-400 text-sm mt-2">
                        上传于 {new Date(doc.created_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span
                        className={`px-3 py-1 rounded-full text-sm ${getStatusColor(
                          doc.status
                        )}`}
                      >
                        {getStatusText(doc.status)}
                      </span>
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
