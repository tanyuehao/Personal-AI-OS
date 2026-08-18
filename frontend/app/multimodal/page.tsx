'use client';

import { useState, useRef } from 'react';
import { multimodalApi, voiceApi } from '@/services/api';
import toast from 'react-hot-toast';

export default function MultimodalPage() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [question, setQuestion] = useState('请描述这张图片的内容');
  const [result, setResult] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      setImagePreview(base64);
      setImageBase64(base64.split(',')[1]);
    };
    reader.readAsDataURL(file);
  };

  const handleAnalyze = async () => {
    if (!imageBase64) return;

    setIsAnalyzing(true);
    try {
      const response = await multimodalApi.analyzeImage({
        image_base64: imageBase64,
        question: question
      });
      setResult(response.data.answer);
    } catch (error) {
      toast.error('图片分析失败');
      setResult('分析失败，请重试');
    }
    setIsAnalyzing(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: Blob[] = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const file = new File([blob], 'audio.webm', { type: 'audio/webm' });

        try {
          const formData = new FormData();
          formData.append('file', file);
          const response = await voiceApi.transcribe(formData);
          setTranscription(response.data.text);
        } catch (error) {
          toast.error('语音转写失败');
        }

        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      toast.error('无法访问麦克风');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">多模态</h1>

        {/* 图片识别 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">图片识别</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div 
                className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-blue-500"
                onClick={() => fileInputRef.current?.click()}
              >
                {imagePreview ? (
                  <img src={imagePreview} alt="预览" className="max-h-64 mx-auto" />
                ) : (
                  <div className="text-gray-500">
                    <div className="text-4xl mb-2">📷</div>
                    <div>点击上传图片</div>
                  </div>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>

            <div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  你想了解什么？
                </label>
                <textarea
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  className="w-full border rounded-lg p-3 h-24 resize-none"
                  placeholder="输入问题..."
                />
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!imageBase64 || isAnalyzing}
                className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isAnalyzing ? '分析中...' : '开始分析'}
              </button>

              {result && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium mb-2">分析结果：</h3>
                  <div className="whitespace-pre-wrap text-gray-700">{result}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 语音输入 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">语音输入</h2>
          
          <div className="text-center">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-24 h-24 rounded-full text-white text-2xl transition ${
                isRecording ? 'bg-red-500 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isRecording ? '⏹️' : '🎤'}
            </button>
            <p className="mt-4 text-gray-500">
              {isRecording ? '正在录音，点击停止...' : '点击开始录音'}
            </p>
          </div>

          {transcription && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium mb-2">识别结果：</h3>
              <div className="text-gray-700">{transcription}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
