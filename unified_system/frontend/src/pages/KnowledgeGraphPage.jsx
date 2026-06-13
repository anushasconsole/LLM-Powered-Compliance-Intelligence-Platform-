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
  const canvasRef = useRef(null);

  useEffect(() => {
    loadGraph();
  }, []);

  useEffect(() => {
    if (graphData) drawGraph();
  }, [graphData, filter]);

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

  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width = canvas.offsetWidth;
    const H = canvas.height = canvas.offsetHeight;

    ctx.clearRect(0, 0, W, H);

    const nodes = filter === 'ALL'
      ? graphData.nodes
      : graphData.nodes.filter(n => n.node_type === filter);

    const nodeIds = new Set(nodes.map(n => n.id));
    const edges = graphData.edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));

    // Simple force-directed layout approximation using random placement
    const positions = {};
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * Math.PI * 2;
      const radius = Math.min(W, H) * 0.35;
      positions[n.id] = {
        x: W / 2 + radius * Math.cos(angle),
        y: H / 2 + radius * Math.sin(angle),
      };
    });

    // Draw edges
    ctx.globalAlpha = 0.3;
    edges.forEach(e => {
      const s = positions[e.from];
      const t = positions[e.to];
      if (!s || !t) return;
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = '#94a3b8';
      ctx.lineWidth = 1;
      ctx.stroke();
    });

    // Draw nodes
    ctx.globalAlpha = 1;
    nodes.forEach(n => {
      const pos = positions[n.id];
      if (!pos) return;
      const color = NODE_COLORS[n.node_type] || '#64748b';
      const radius = n.node_type === 'FRAMEWORK' ? 12 : n.node_type === 'POLICY' ? 10 : 7;

      // Glow
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Label (only for important nodes)
      if (n.node_type === 'FRAMEWORK' || n.node_type === 'POLICY') {
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(n.name?.slice(0, 12) || n.id?.slice(0, 8), pos.x, pos.y - radius - 4);
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
      <div className="glass-effect rounded-2xl border border-white/10 p-4 flex flex-wrap items-center gap-4">
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
        <div className="ml-auto flex flex-wrap gap-3">
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
          <canvas ref={canvasRef} className="w-full h-full" style={{ background: 'transparent' }} />
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

