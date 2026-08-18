'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { graphApi } from '@/services/api';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  group: number;
  data?: any;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
  type?: string;
}

const TYPE_COLORS: Record<string, string> = {
  document: '#3b82f6',
  memory: '#10b981',
  belief: '#8b5cf6',
  decision: '#f59e0b',
  chunk: '#6b7280',
};

const TYPE_LABELS: Record<string, string> = {
  document: '文档',
  memory: '记忆',
  belief: '观点',
  decision: '决策',
  chunk: '知识切片',
};

export default function GraphPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: 800, h: 600 });
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await graphApi.getData();
      const data = res.data;

      // 初始化节点位置（力导向布局简化版）
      const initializedNodes = data.nodes.map((node: GraphNode, i: number) => {
        const angle = (2 * Math.PI * i) / data.nodes.length;
        const radius = 200 + Math.random() * 100;
        return {
          ...node,
          x: 400 + radius * Math.cos(angle),
          y: 300 + radius * Math.sin(angle),
          vx: 0,
          vy: 0,
        };
      });

      setNodes(initializedNodes);
      setEdges(data.edges);
      setStats(data.stats);
    } catch (error) {
      console.error('Failed to load graph data:', error);
    }
    setLoading(false);
  };

  // 简化的力导向布局
  const simulateLayout = useCallback(() => {
    setNodes(prevNodes => {
      const newNodes = prevNodes.map(n => ({ ...n }));
      const k = 0.01; // 弹性系数
      const repulsion = 5000; // 排斥力
      const damping = 0.9; // 阻尼

      for (let i = 0; i < newNodes.length; i++) {
        let fx = 0, fy = 0;

        // 斥力（所有节点之间）
        for (let j = 0; j < newNodes.length; j++) {
          if (i === j) continue;
          const dx = (newNodes[i].x || 0) - (newNodes[j].x || 0);
          const dy = (newNodes[i].y || 0) - (newNodes[j].y || 0);
          const dist = Math.sqrt(dx * dx + dy * dy) + 1;
          fx += (repulsion * dx) / (dist * dist);
          fy += (repulsion * dy) / (dist * dist);
        }

        // 引力（连接的节点之间）
        for (const edge of edges) {
          let other = null;
          if (edge.source === newNodes[i].id) {
            other = newNodes.find(n => n.id === edge.target);
          } else if (edge.target === newNodes[i].id) {
            other = newNodes.find(n => n.id === edge.source);
          }
          if (other) {
            const dx = (other.x || 0) - (newNodes[i].x || 0);
            const dy = (other.y || 0) - (newNodes[i].y || 0);
            fx += k * dx;
            fy += k * dy;
          }
        }

        // 中心引力
        fx += (400 - (newNodes[i].x || 0)) * 0.001;
        fy += (300 - (newNodes[i].y || 0)) * 0.001;

        // 更新速度和位置
        if (newNodes[i].id !== draggingNode) {
          newNodes[i].vx = ((newNodes[i].vx || 0) + fx) * damping;
          newNodes[i].vy = ((newNodes[i].vy || 0) + fy) * damping;
          newNodes[i].x = (newNodes[i].x || 0) + (newNodes[i].vx || 0);
          newNodes[i].y = (newNodes[i].y || 0) + (newNodes[i].vy || 0);
        }
      }

      return newNodes;
    });
  }, [edges, draggingNode]);

  useEffect(() => {
    if (nodes.length === 0) return;
    const timer = setInterval(simulateLayout, 50);
    return () => clearInterval(timer);
  }, [nodes.length, simulateLayout]);

  const handleMouseDown = (nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setDraggingNode(nodeId);
      setOffset({
        x: e.clientX - (node.x || 0),
        y: e.clientY - (node.y || 0),
      });
      setSelectedNode(node);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingNode || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setNodes(prev =>
      prev.map(n =>
        n.id === draggingNode ? { ...n, x, y, vx: 0, vy: 0 } : n
      )
    );
  };

  const handleMouseUp = () => {
    setDraggingNode(null);
  };

  const getNodePos = (id: string) => {
    const node = nodes.find(n => n.id === id);
    return { x: node?.x || 0, y: node?.y || 0 };
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">🔗 知识图谱</h1>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            刷新
          </button>
        </div>

        {/* 图例 */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4 flex items-center gap-6 flex-wrap">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-sm text-gray-600">{TYPE_LABELS[type]}</span>
            </div>
          ))}
          <div className="ml-auto text-sm text-gray-400">
            拖拽节点 · 点击查看详情
          </div>
        </div>

        <div className="flex gap-4">
          {/* 图谱区域 */}
          <div className="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-96">
                <div className="text-gray-500">加载中...</div>
              </div>
            ) : nodes.length === 0 ? (
              <div className="flex items-center justify-center h-96 text-gray-500">
                暂无数据，请先添加文档、记忆或观点
              </div>
            ) : (
              <svg
                ref={svgRef}
                className="w-full h-[600px] cursor-grab active:cursor-grabbing"
                viewBox="0 0 800 600"
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                {/* 边 */}
                <g>
                  {edges.map((edge, i) => {
                    const from = getNodePos(edge.source);
                    const to = getNodePos(edge.target);
                    const isHighlighted =
                      hoveredNode === edge.source || hoveredNode === edge.target;
                    return (
                      <g key={i}>
                        <line
                          x1={from.x}
                          y1={from.y}
                          x2={to.x}
                          y2={to.y}
                          stroke={isHighlighted ? '#3b82f6' : '#e5e7eb'}
                          strokeWidth={isHighlighted ? 2 : 1}
                        />
                        {edge.label && (
                          <text
                            x={(from.x + to.x) / 2}
                            y={(from.y + to.y) / 2 - 5}
                            textAnchor="middle"
                            className="text-[10px] fill-gray-400"
                          >
                            {edge.label}
                          </text>
                        )}
                      </g>
                    );
                  })}
                </g>

                {/* 节点 */}
                <g>
                  {nodes.map(node => {
                    const color = TYPE_COLORS[node.type] || '#6b7280';
                    const isHovered = hoveredNode === node.id;
                    const isSelected = selectedNode?.id === node.id;
                    const radius = node.type === 'chunk' ? 8 : isHovered || isSelected ? 18 : 14;
                    return (
                      <g
                        key={node.id}
                        onMouseDown={(e) => handleMouseDown(node.id, e)}
                        onMouseEnter={() => setHoveredNode(node.id)}
                        onMouseLeave={() => setHoveredNode(null)}
                        className="cursor-pointer"
                      >
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r={radius}
                          fill={color}
                          stroke={isSelected ? '#1d4ed8' : '#fff'}
                          strokeWidth={isSelected ? 3 : 2}
                          opacity={node.type === 'chunk' ? 0.6 : 1}
                        />
                        {(isHovered || isSelected || node.type !== 'chunk') && (
                          <text
                            x={node.x}
                            y={(node.y || 0) + radius + 14}
                            textAnchor="middle"
                            className="text-[11px] fill-gray-700 pointer-events-none select-none"
                            style={{ fontWeight: isSelected ? 600 : 400 }}
                          >
                            {node.label.length > 15
                              ? node.label.substring(0, 15) + '...'
                              : node.label}
                          </text>
                        )}
                      </g>
                    );
                  })}
                </g>
              </svg>
            )}
          </div>

          {/* 详情面板 */}
          <div className="w-80 bg-white rounded-lg shadow-sm p-4">
            <h2 className="text-lg font-semibold mb-4">详情</h2>
            {selectedNode ? (
              <div className="space-y-3">
                <div>
                  <span
                    className="inline-block px-2 py-1 rounded text-white text-xs"
                    style={{ backgroundColor: TYPE_COLORS[selectedNode.type] }}
                  >
                    {TYPE_LABELS[selectedNode.type]}
                  </span>
                </div>
                <div>
                  <div className="text-sm text-gray-500">名称</div>
                  <div className="font-medium">{selectedNode.label}</div>
                </div>
                {selectedNode.data && (
                  <>
                    {selectedNode.data.content && (
                      <div>
                        <div className="text-sm text-gray-500">内容</div>
                        <div className="text-sm">{selectedNode.data.content}</div>
                      </div>
                    )}
                    {selectedNode.data.summary && (
                      <div>
                        <div className="text-sm text-gray-500">摘要</div>
                        <div className="text-sm">{selectedNode.data.summary}</div>
                      </div>
                    )}
                    {selectedNode.data.memory_type && (
                      <div>
                        <div className="text-sm text-gray-500">类型</div>
                        <div className="text-sm">{selectedNode.data.memory_type}</div>
                      </div>
                    )}
                    {selectedNode.data.importance !== undefined && (
                      <div>
                        <div className="text-sm text-gray-500">重要性</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${selectedNode.data.importance * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {selectedNode.data.confidence !== undefined && (
                      <div>
                        <div className="text-sm text-gray-500">可信度</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-purple-500 h-2 rounded-full"
                            style={{ width: `${selectedNode.data.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {selectedNode.data.choice && (
                      <div>
                        <div className="text-sm text-gray-500">选择</div>
                        <div className="text-sm">{selectedNode.data.choice}</div>
                      </div>
                    )}
                    {selectedNode.data.reasoning && (
                      <div>
                        <div className="text-sm text-gray-500">理由</div>
                        <div className="text-sm">{selectedNode.data.reasoning}</div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="text-gray-400 text-sm">点击节点查看详情</div>
            )}

            {/* 统计信息 */}
            {stats && (
              <div className="mt-6 pt-4 border-t">
                <h3 className="text-sm font-medium text-gray-500 mb-3">统计</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>文档</span>
                    <span className="font-medium">{stats.documents}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>记忆</span>
                    <span className="font-medium">{stats.memories}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>观点</span>
                    <span className="font-medium">{stats.beliefs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>决策</span>
                    <span className="font-medium">{stats.decisions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>关系</span>
                    <span className="font-medium">{stats.total_edges}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
