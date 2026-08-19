'use client';

import { useState, useEffect } from 'react';
import { documentApi } from '@/services/api';
import toast from 'react-hot-toast';

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
      setDocuments(response.data.items || []);
    } catch (error) {
      toast.error('加载文档失败');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', '默认分类');

      await documentApi.upload(formData);
      
      toast.success('上传成功！');
      await loadDocuments();
    } catch (error) {
      toast.error('上传失败');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('确定要删除这个文档吗？')) return;

    try {
      await documentApi.delete(documentId);
      toast.success('删除成功');
      await loadDocuments();
    } catch (error) {
      toast.error('删除失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'badge-success';
      case 'PROCESSING': return 'badge-warning';
      case 'FAILED': return 'badge-danger';
      default: return 'badge-primary';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'UPLOADING': return '上传中';
      case 'PROCESSING': return '处理中';
      case 'COMPLETED': return '已完成';
      case 'FAILED': return '失败';
      default: return status;
    }
  };

  return (
    <div className="p-8 animate-fade-in">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">📚 知识库管理</h1>

        {/* 上传区域 */}
        <div className="card mb-8">
          <h2 className="card-header">上传文档</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-500 transition-colors cursor-pointer">
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
              className="cursor-pointer"
            >
              {isUploading ? (
                <div className="text-blue-600">
                  <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-lg font-medium">正在上传...</p>
                </div>
              ) : (
                <>
                  <div className="text-6xl mb-4">📁</div>
                  <p className="text-lg font-medium text-gray-700">点击或拖拽文件到此处上传</p>
                  <p className="text-gray-500 mt-2">支持格式：PDF, Word, Markdown, TXT, CSV, Excel</p>
                  <p className="text-gray-500">最大文件大小：50MB</p>
                </>
              )}
            </label>
          </div>
        </div>

        {/* 文档列表 */}
        <div className="card">
          <h2 className="card-header">文档列表</h2>
          
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-gray-500">还没有上传任何文档</p>
              <p className="text-gray-400 text-sm mt-2">点击上方上传按钮开始</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map(doc => (
                <div
                  key={doc.document_id}
                  className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <span className="text-xl">📄</span>
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">{doc.file_name}</h3>
                          <p className="text-sm text-gray-500">
                            {doc.file_type.toUpperCase()} • {(doc.file_size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      {doc.summary && (
                        <p className="text-gray-600 mt-3 ml-13 line-clamp-2">{doc.summary}</p>
                      )}
                      <p className="text-gray-400 text-sm mt-2 ml-13">
                        上传于 {new Date(doc.created_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`badge ${getStatusColor(doc.status)}`}>
                        {getStatusText(doc.status)}
                      </span>
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        className="btn btn-ghost text-red-600 hover:text-red-700"
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
