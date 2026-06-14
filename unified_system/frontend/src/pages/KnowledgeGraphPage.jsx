import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Network, RefreshCw, Filter, Info } from 'lucide-react';
import { knowledgeGraphAPI } from '../api/client.jsx';

const NODE_COLORS = {
  POLICY: '#8b5cf6',
  REQUIREMENT: '#3b82f6',
  EVIDENCE: '#10b981',
  FRAMEWORK: '#f59e0b',
  TEAM: '#ec4899',
  CONTROL_AREA: '#06b6d4',
};

const StatCard = ({ label, value, color }) => (
  <div className="glass-effect rounded-xl p-4 border border-white/10 text-center">
    <div className="text-2xl font-bold" style={{ color }}>{value}</div>
    <div className="text-xs text-gray-400 mt-1">{label}</div>
  </div>
);

const KnowledgeGraphPage = () => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('ALL');
  const [showEvidence, setShowEvidence] = useState(true); // Changed to true by default
  const [hoveredNode, setHoveredNode] = useState(null);
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    loadGraph();
  }, []);

  useEffect(() => {
    if (graphData) drawGraph();
  }, [graphData, filter, showEvidence, hoveredNode]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseMove = (e) => {
      if (!graphData) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Find hovered node
      const nodes = getFilteredNodes();
      const positions = calculatePositions(nodes, canvas.width, canvas.height);
      
      let found = null;
      for (const n of nodes) {
        const pos = positions[n.id];
        if (!pos) continue;
        const radius = getNodeRadius(n.node_type);
        const dist = Math.sqrt((x - pos.x)**2 + (y - pos.y)**2);
        if (dist < radius + 5) {
          found = n;
          break;
        }
      }
      setHoveredNode(found);
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    return () => canvas.removeEventListener('mousemove', handleMouseMove);
  }, [graphData, filter, showEvidence]);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await knowledgeGraphAPI.get();
      setGraphData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getNodeRadius = (nodeType) => {
    if (nodeType === 'FRAMEWORK') return 14;
    if (nodeType === 'POLICY') return 12;
    if (nodeType === 'REQUIREMENT') return 10;
    if (nodeType === 'EVIDENCE') return 5; // Smaller for evidence
    return 8;
  };

  const getFilteredNodes = () => {
    if (!graphData) return [];
    let nodes = graphData.nodes;
    if (!showEvidence) {
      nodes = nodes.filter(n => n.node_type !== 'EVIDENCE');
    }
    if (filter !== 'ALL') {
      nodes = nodes.filter(n => n.node_type === filter);
    }
    return nodes;
  };

  const calculatePositions = (nodes, W, H) => {
    const positions = {};
    const nodesByType = {};
    
    nodes.forEach(n => {
      if (!nodesByType[n.node_type]) nodesByType[n.node_type] = [];
      nodesByType[n.node_type].push(n);
    });

    const hierarchy = ['FRAMEWORK', 'POLICY', 'REQUIREMENT', 'CONTROL_AREA', 'TEAM', 'EVIDENCE'];
    
    // Calculate how many layers we actually have
    const activeLayers = hierarchy.filter(type => nodesByType[type] && nodesByType[type].length > 0);
    const layerHeight = H / (activeLayers.length + 1);
    let currentLayer = 1;

    hierarchy.forEach(type => {
      const typeNodes = nodesByType[type] || [];
      if (typeNodes.length === 0) return;
      
      const y = layerHeight * currentLayer;
      
      // Spacing calculation
      let minSpacing = 30; // Default small spacing for evidence
      if (type === 'FRAMEWORK') minSpacing = 140;
      else if (type === 'REQUIREMENT') minSpacing = 60;
      else if (type === 'POLICY') minSpacing = 100;
      
      // For evidence nodes, use very tight spacing and multiple rows if needed
      if (type === 'EVIDENCE' && typeNodes.length > 50) {
        // Arrange evidence in multiple rows
        const nodesPerRow = Math.ceil(Math.sqrt(typeNodes.length));
        const rowSpacing = 25;
        const colSpacing = 30;
        const rows = Math.ceil(typeNodes.length / nodesPerRow);
        const startY = y - ((rows - 1) * rowSpacing) / 2;
        
        typeNodes.forEach((n, i) => {
          const row = Math.floor(i / nodesPerRow);
          const col = i % nodesPerRow;
          const rowWidth = Math.min(nodesPerRow, typeNodes.length - row * nodesPerRow) * colSpacing;
          const startX = (W - rowWidth) / 2;
          
          positions[n.id] = {
            x: startX + (col * colSpacing),
            y: startY + (row * rowSpacing)
          };
        });
      } else {
        // Normal single-row layout for other types
        const requiredWidth = minSpacing * typeNodes.length;
        const spacing = requiredWidth > W ? W / (typeNodes.length + 1) : minSpacing;
        const totalWidth = spacing * (typeNodes.length - 1);
        const startX = (W - totalWidth) / 2;
        
        typeNodes.forEach((n, i) => {
          positions[n.id] = { x: startX + (i * spacing), y: y };
        });
      }
      
      currentLayer++;
    });

    return positions;
  };

  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = canvas.offsetWidth;
    const H = canvas.height = canvas.offsetHeight;

    ctx.clearRect(0, 0, W, H);

    const nodes = getFilteredNodes();
    const nodeIds = new Set(nodes.map(n => n.id));
    const edges = graphData.edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
    const positions = calculatePositions(nodes, W, H);

    // Draw edges with varying opacity based on node type
    edges.forEach(e => {
      const s = positions[e.from];
      const t = positions[e.to];
      if (!s || !t) return;
      
      const fromNode = nodes.find(n => n.id === e.from);
      const toNode = nodes.find(n => n.id === e.to);
      
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      const cx = (s.x + t.x) / 2;
      const cy = (s.y + t.y) / 2;
      ctx.quadraticCurveTo(cx + 20, cy, t.x, t.y);
      
      // Lighter edges for evidence connections
      if (fromNode?.node_type === 'EVIDENCE' || toNode?.node_type === 'EVIDENCE') {
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 0.5;
        ctx.globalAlpha = 0.15;
      } else {
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.4;
      }
      ctx.stroke();
      ctx.globalAlpha = 1;
    });

    // Draw nodes
    nodes.forEach(n => {
      const pos = positions[n.id];
      if (!pos) return;
      const color = NODE_COLORS[n.node_type] || '#64748b';
      const radius = getNodeRadius(n.node_type);
      const isHovered = hoveredNode && hoveredNode.id === n.id;

      // Glow effect
      ctx.shadowColor = color;
      ctx.shadowBlur = isHovered ? 25 : 15;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isHovered ? radius + 2 : radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = isHovered ? '#fff' : '#1e293b';
      ctx.lineWidth = isHovered ? 3 : 2;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Only show labels for FRAMEWORK nodes (top row)
      if (n.node_type === 'FRAMEWORK') {
        const label = (n.name || n.id || '').slice(0, 12);
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        const textWidth = ctx.measureText(label).width;
        const padding = 6;
        
        ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
        ctx.fillRect(pos.x - textWidth/2 - padding, pos.y - radius - 20, textWidth + padding*2, 16);
        
        ctx.fillStyle = '#f8fafc';
        ctx.fillText(label, pos.x, pos.y - radius - 8);
      }
    });
  };

  const stats = graphData?.stats || {};
  const typeFilters = ['ALL', 'POLICY', 'REQUIREMENT', 'EVIDENCE', 'FRAMEWORK'];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-cyan-600 via-blue-600 to-purple-600"
      >
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Network className="w-10 h-10" />
            <div>
              <h1 className="text-4xl font-bold">Knowledge Graph</h1>
              <p className="text-blue-100 mt-1">Enterprise compliance relationships visualized</p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={loadGraph}
            disabled={loading}
            className="flex items-center space-x-2 px-5 py-3 rounded-xl bg-white/20 hover:bg-white/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Nodes" value={stats.total_nodes || 0} color="#8b5cf6" />
        <StatCard label="Requirements" value={stats.requirements || 0} color="#3b82f6" />
        <StatCard label="Evidence" value={stats.evidence || 0} color="#10b981" />
        <StatCard label="Frameworks" value={stats.frameworks || 0} color="#f59e0b" />
      </div>

      {/* Legend + Filter */}
      <div className="glass-effect rounded-2xl border border-white/10 p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2 text-sm text-gray-300">
            <Filter className="w-4 h-4" />
            <span>Filter:</span>
          </div>
          {typeFilters.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === f
                  ? 'text-white'
                  : 'text-gray-400 hover:text-white bg-white/5 hover:bg-white/10'
              }`}
              style={filter === f ? { backgroundColor: NODE_COLORS[f] || '#8b5cf6' } : {}}
            >
              {f}
            </button>
          ))}
          <div className="ml-auto">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showEvidence}
                onChange={(e) => setShowEvidence(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-sm text-gray-300">Show Evidence Nodes (500)</span>
            </label>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 pt-2 border-t border-white/5">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center space-x-1.5 text-xs text-gray-400">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span>{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div className="glass-effect rounded-2xl border border-white/10 overflow-hidden" style={{ height: '520px' }}>
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <RefreshCw className="w-10 h-10 animate-spin text-purple-400 mx-auto mb-4" />
              <p className="text-gray-400">Loading knowledge graph...</p>
            </div>
          </div>
        ) : !graphData ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-500">
              <Network className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Initialize the system first to build the knowledge graph.</p>
            </div>
          </div>
        ) : (
          <div className="relative h-full">
            <canvas ref={canvasRef} className="w-full h-full" style={{ background: 'transparent', cursor: hoveredNode ? 'pointer' : 'default' }} />
            {showEvidence && (
              <div className="absolute top-4 left-4 bg-green-500/20 border border-green-400/30 rounded-lg px-4 py-2 text-sm text-green-200">
                <Info className="w-4 h-4 inline mr-2" />
                Showing all {stats.evidence || 0} evidence nodes (green dots in grid at bottom)
              </div>
            )}
            {hoveredNode && (
              <div 
                className="absolute bg-gray-900/95 border border-gray-700 rounded-lg px-4 py-3 text-sm shadow-xl z-10"
                style={{ top: '20px', right: '20px', maxWidth: '300px' }}
              >
                <div className="font-bold text-white mb-1">{hoveredNode.name || hoveredNode.id}</div>
                <div className="text-xs text-gray-400 mb-2">Type: {hoveredNode.node_type}</div>
                {hoveredNode.description && (
                  <div className="text-xs text-gray-300">{hoveredNode.description.slice(0, 100)}...</div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Edge types */}
      <div className="glass-effect rounded-2xl border border-white/10 p-5">
        <h3 className="font-semibold text-gray-300 mb-3 flex items-center space-x-2">
          <Info className="w-4 h-4 text-blue-400" />
          <span>Relationship Types</span>
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { rel: 'CONTAINS', desc: 'Policy → Requirement', color: '#8b5cf6' },
            { rel: 'SUPPORTS', desc: 'Evidence → Requirement', color: '#10b981' },
            { rel: 'MAPS_TO', desc: 'Requirement → Framework', color: '#f59e0b' },
            { rel: 'OWNED_BY', desc: 'Requirement → Team', color: '#ec4899' },
          ].map(r => (
            <div key={r.rel} className="bg-white/5 rounded-xl p-3 border border-white/5">
              <div className="font-mono text-xs font-bold mb-1" style={{ color: r.color }}>{r.rel}</div>
              <div className="text-xs text-gray-400">{r.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;

