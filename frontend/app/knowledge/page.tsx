'use client';

import { useState, useEffect, useRef } from 'react';
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
  const [dragActive, setDragActive] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  // 处理上传队列
  useEffect(() => {
    if (uploadQueue.length > 0 && !isUploading) {
      uploadNextFile();
    }
  }, [uploadQueue, isUploading]);

  const loadDocuments = async () => {
    try {
      const response = await documentApi.list();
      setDocuments(response.data.items);
    } catch (error) {
      toast.error('加载文档失败');
    }
  };

  const uploadNextFile = async () => {
    if (uploadQueue.length === 0) return;

    setIsUploading(true);
    const file = uploadQueue[0];
    const remaining = uploadQueue.slice(1);
    setUploadQueue(remaining);

    try {
      const formData = new FormData();
      formData.append('file', file);

      await documentApi.upload(formData);
      await loadDocuments();
    } catch (error) {
      toast.error(`${file.name} 上传失败`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFiles = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const allowedTypes = ['.pdf', '.doc', '.docx', '.md', '.txt', '.csv', '.xlsx', '.xls'];

    const validFiles = fileArray.filter(file => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowedTypes.includes(ext)) {
        toast.error(`${file.name} 格式不支持`);
        return false;
      }
      if (file.size > 50 * 1024 * 1024) {
        toast.error(`${file.name} 超过 50MB 限制`);
        return false;
      }
      return true;
    });

    if (validFiles.length > 0) {
      setUploadQueue(prev => [...prev, ...validFiles]);
    }
  };

  // 拖拽事件
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragActive(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
      e.target.value = '';
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('确定要删除这个文档吗？')) return;

    try {
      await documentApi.delete(documentId);
      await loadDocuments();
    } catch (error) {
      toast.error('删除失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'bg-green-100 text-green-800';
      case 'PROCESSING': return 'bg-yellow-100 text-yellow-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
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

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">📚 知识库管理</h1>

        {/* 拖拽上传区域 */}
        <div
          className={`bg-white rounded-lg shadow-md p-6 mb-8 transition-all ${
            dragActive ? 'ring-4 ring-blue-400 bg-blue-50' : ''
          }`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="border-2 border-dashed rounded-lg p-12 text-center transition-colors">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.doc,.docx,.md,.txt,.csv,.xlsx,.xls"
              multiple
              onChange={handleFileInput}
            />

            {isUploading ? (
              <div className="space-y-4">
                <div className="text-4xl">⏳</div>
                <p className="text-lg font-medium text-blue-600">正在上传...</p>
                {uploadQueue.length > 0 && (
                  <p className="text-sm text-gray-500">
                    还剩 {uploadQueue.length} 个文件
                  </p>
                )}
              </div>
            ) : dragActive ? (
              <div className="space-y-4">
                <div className="text-4xl">📥</div>
                <p className="text-lg font-medium text-blue-600">松开鼠标上传文件</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-4xl">📄</div>
                <p className="text-lg font-medium text-gray-700">
                  拖拽文件到这里，或者{' '}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    点击选择
                  </button>
                </p>
                <p className="text-sm text-gray-500">
                  支持 PDF、Word、Markdown、TXT、CSV、Excel（最大 50MB）
                </p>
                <p className="text-sm text-gray-500">支持批量上传多个文件</p>
              </div>
            )}
          </div>
        </div>

        {/* 文档列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">文档列表</h2>
            <span className="text-sm text-gray-500">{documents.length} 个文档</span>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-4">📭</div>
              <p>还没有上传任何文档</p>
              <p className="text-sm mt-2">拖拽文件到上方区域开始上传</p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow flex items-start gap-4"
                >
                  {/* 文件图标 */}
                  <div className="text-3xl">
                    {doc.file_type === '.pdf' ? '📕' :
                     doc.file_type === '.doc' || doc.file_type === '.docx' ? '📘' :
                     doc.file_type === '.md' ? '📝' :
                     doc.file_type === '.csv' || doc.file_type === '.xlsx' || doc.file_type === '.xls' ? '📊' :
                     '📄'}
                  </div>

                  {/* 文件信息 */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{doc.file_name}</h3>
                    <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                      <span>{doc.file_type.toUpperCase()}</span>
                      <span>•</span>
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{new Date(doc.created_at).toLocaleDateString('zh-CN')}</span>
                    </div>
                    {doc.summary && (
                      <p className="text-gray-600 text-sm mt-2 line-clamp-2">{doc.summary}</p>
                    )}
                  </div>

                  {/* 状态和操作 */}
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(doc.status)}`}>
                      {getStatusText(doc.status)}
                    </span>
                    <button
                      onClick={() => handleDelete(doc.document_id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="删除"
                    >
                      🗑️
                    </button>
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
