'use client';

import { useState, useEffect, useRef } from 'react';
import { documentApi, cognitiveApi, memoryApi } from '@/services/api';

interface GraphNode {
  id: string;
  label: string;
  type: 'document' | 'memory' | 'belief' | 'decision';
  group: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    loadGraphData();
  }, []);

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      drawGraph();
    }
  }, [graphData]);

  const loadGraphData = async () => {
    try {
      const nodes: GraphNode[] = [];
      const edges: GraphEdge[] = [];

      // 获取文档
      const docs = await documentApi.list({ limit: 50 });
      docs.data.items?.forEach((doc: any, i: number) => {
        nodes.push({ id: `doc_${doc.document_id}`, label: doc.file_name, type: 'document', group: 1 });
      });

      // 获取记忆
      const memories = await memoryApi.list({ limit: 20 });
      memories.data.items?.forEach((mem: any) => {
        nodes.push({ id: `mem_${mem.memory_id}`, label: mem.content.substring(0, 20) + '...', type: 'memory', group: 2 });
      });

      // 获取观点
      const beliefs = await cognitiveApi.listBeliefs({ limit: 20 });
      beliefs.data.items?.forEach((belief: any) => {
        nodes.push({ id: `belief_${belief.belief_id}`, label: belief.topic, type: 'belief', group: 3 });
      });

      // 生成一些示例关系
      if (nodes.length > 1) {
        for (let i = 1; i < Math.min(nodes.length, 10); i++) {
          edges.push({ source: nodes[0].id, target: nodes[i].id, label: '相关' });
        }
      }

      setGraphData({ nodes, edges });
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;

    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 3;

    // 计算节点位置
    const nodePositions: Record<string, { x: number; y: number }> = {};
    graphData.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / graphData.nodes.length - Math.PI / 2;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    // 绘制边
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    graphData.edges.forEach(edge => {
      const from = nodePositions[edge.source];
      const to = nodePositions[edge.target];
      if (from && to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      }
    });

    // 绘制节点
    const colors: Record<number, string> = { 1: '#3b82f6', 2: '#10b981', 3: '#8b5cf6', 4: '#f59e0b' };
    graphData.nodes.forEach(node => {
      const pos = nodePositions[node.id];
      if (pos) {
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 20, 0, 2 * Math.PI);
        ctx.fillStyle = colors[node.group] || '#666';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 绘制标签
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        const label = node.label.length > 10 ? node.label.substring(0, 10) + '...' : node.label;
        ctx.fillText(label, pos.x, pos.y + 35);
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">知识图谱</h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500"></div>
              <span className="text-sm">文档</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <span className="text-sm">记忆</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-purple-500"></div>
              <span className="text-sm">观点</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
              <span className="text-sm">决策</span>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">加载中...</div>
          ) : graphData.nodes.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              暂无数据，请先添加文档、记忆或观点
            </div>
          ) : (
            <canvas ref={canvasRef} className="w-full h-96 border rounded-lg" />
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">知识统计</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {graphData.nodes.filter(n => n.type === 'document').length}
              </div>
              <div className="text-sm text-gray-600">文档</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {graphData.nodes.filter(n => n.type === 'memory').length}
              </div>
              <div className="text-sm text-gray-600">记忆</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {graphData.nodes.filter(n => n.type === 'belief').length}
              </div>
              <div className="text-sm text-gray-600">观点</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {graphData.edges.length}
              </div>
              <div className="text-sm text-gray-600">关系</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
