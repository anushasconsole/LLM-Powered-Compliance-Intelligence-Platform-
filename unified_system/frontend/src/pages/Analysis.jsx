import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Play, CheckCircle, AlertTriangle, XCircle, TrendingUp, RefreshCw } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { analysisAPI } from '../api/client.jsx';

const FRAMEWORKS = [
  { name: 'GDPR', color: '#10b981' },
  { name: 'SOX', color: '#3b82f6' },
  { name: 'NIST', color: '#8b5cf6' },
  { name: 'PCI-DSS', color: '#ec4899' },
  { name: 'ISO27001', color: '#f59e0b' },
  { name: 'HIPAA', color: '#06b6d4' },
  { name: 'ALL', color: '#64748b' },
];

const Analysis = () => {
  const [selectedFramework, setSelectedFramework] = useState('GDPR');
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState(null);

  const runAnalysis = async () => {
    setIsRunning(true);
    setResults(null);
    try {
      const res = await analysisAPI.run(selectedFramework);
      const data = res.data;
      setResults({
        framework: data.framework,
        overallScore: data.compliance_score || 0,
        requirementsAnalyzed: data.requirements_analyzed || 0,
        requirementsCovered: data.requirements_covered || 0,
        averageConfidence: data.average_confidence || 0,
        gaps: data.requirements_with_gaps || 0,
        status: data.status || 'UNKNOWN',
        gapList: data.gaps || [],
        coveragePercentage: data.coverage_percentage || '0%',
      });
    } catch (e) {
      console.error('Analysis error:', e);
      setResults({ error: String(e) });
    } finally {
      setIsRunning(false);
    }
  };

  const fwColor = FRAMEWORKS.find(f => f.name === selectedFramework)?.color || '#8b5cf6';

  const chartData = results ? [
    { name: 'Covered', value: results.requirementsCovered, fill: '#10b981' },
    { name: 'Gaps', value: results.gaps, fill: '#ef4444' },
  ] : [];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-green-600 via-emerald-600 to-teal-600"
      >
        <div className="relative z-10">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-4">
              <motion.div animate={{ rotate: [0, 360] }} transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}>
                <BarChart3 className="w-10 h-10" />
              </motion.div>
              <div>
                <h1 className="text-4xl font-bold">Compliance Analysis</h1>
                <p className="text-green-100 mt-1">LLM-extracted requirements → Semantic mapping → Scoring</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <select
                value={selectedFramework}
                onChange={e => setSelectedFramework(e.target.value)}
                className="px-4 py-2 rounded-xl bg-white/20 border border-white/20 focus:outline-none text-sm font-medium"
              >
                {FRAMEWORKS.map(f => (
                  <option key={f.name} value={f.name} className="bg-slate-900">{f.name}</option>
                ))}
              </select>
              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={runAnalysis} disabled={isRunning}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 font-medium disabled:opacity-50"
              >
                {isRunning
                  ? <RefreshCw className="w-5 h-5 animate-spin" />
                  : <Play className="w-5 h-5" />
                }
                <span>{isRunning ? 'Analysing...' : 'Run Analysis'}</span>
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* No results yet */}
      {!results && !isRunning && (
        <div className="glass-effect rounded-2xl border border-white/10 p-16 text-center">
          <BarChart3 className="w-16 h-16 text-emerald-400 mx-auto mb-4 opacity-40" />
          <h3 className="text-xl font-semibold text-gray-300 mb-2">Ready to Analyse</h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Select a compliance framework and click "Run Analysis" to get real scores
            from the backend pipeline.
          </p>
        </div>
      )}

      {/* Loading */}
      {isRunning && (
        <div className="glass-effect rounded-2xl border border-white/10 p-16 text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-emerald-400 mx-auto mb-4" />
          <p className="text-gray-400">Running compliance analysis for <strong>{selectedFramework}</strong>…</p>
        </div>
      )}

      {/* Error */}
      {results?.error && (
        <div className="glass-effect rounded-2xl border border-red-500/30 p-6 text-red-400">
          Error: {results.error}
        </div>
      )}

      {/* Results */}
      {results && !results.error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* Score cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Compliance Score', value: `${results.overallScore.toFixed(1)}%`, icon: TrendingUp, color: fwColor },
              { label: 'Requirements Analysed', value: results.requirementsAnalyzed, icon: CheckCircle, color: '#3b82f6' },
              { label: 'Requirements Covered', value: results.requirementsCovered, icon: CheckCircle, color: '#10b981' },
              { label: 'Gaps Found', value: results.gaps, icon: AlertTriangle, color: '#ef4444' },
            ].map((card, i) => {
              const Icon = card.icon;
              return (
                <motion.div
                  key={i} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="glass-effect rounded-xl border border-white/10 p-5 text-center"
                >
                  <Icon className="w-7 h-7 mx-auto mb-2" style={{ color: card.color }} />
                  <div className="text-2xl font-bold" style={{ color: card.color }}>{card.value}</div>
                  <div className="text-xs text-gray-400 mt-1">{card.label}</div>
                </motion.div>
              );
            })}
          </div>

          {/* Status badge */}
          <div className="flex items-center space-x-3">
            <span className={`px-4 py-2 rounded-xl text-sm font-semibold border ${
              results.status === 'COMPLIANT'
                ? 'bg-green-500/10 text-green-400 border-green-500/30'
                : 'bg-red-500/10 text-red-400 border-red-500/30'
            }`}>
              {results.status === 'COMPLIANT' ? '✅' : '❌'} {results.status}
            </span>
            <span className="text-gray-400 text-sm">Coverage: {results.coveragePercentage}</span>
            <span className="text-gray-400 text-sm">Avg Confidence: {(results.averageConfidence * 100).toFixed(0)}%</span>
          </div>

          {/* Chart */}
          <div className="glass-effect rounded-2xl border border-white/10 p-6">
            <h3 className="text-lg font-semibold mb-4">Coverage Breakdown</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} layout="vertical">
                <XAxis type="number" stroke="#64748b" />
                <YAxis type="category" dataKey="name" stroke="#64748b" width={80} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Gap list */}
          {results.gapList.length > 0 && (
            <div className="glass-effect rounded-2xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                <XCircle className="w-5 h-5 text-red-400" />
                <span>Compliance Gaps ({results.gapList.length})</span>
              </h3>
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {results.gapList.map((gap, i) => (
                  <div key={i} className="flex items-start space-x-3 p-3 rounded-xl bg-red-500/5 border border-red-500/10">
                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-mono text-xs text-red-300">{gap.requirement_id}</span>
                      <p className="text-sm text-gray-300 mt-0.5">{gap.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Analysis;

