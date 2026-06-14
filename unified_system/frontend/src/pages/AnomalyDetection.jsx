import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertOctagon, Play, RefreshCw, CheckCircle, XCircle,
  AlertTriangle, Clock, TrendingUp, BarChart2, Target, Zap,
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
  PieChart, Pie,
} from 'recharts';
import { anomalyAPI } from '../api/client.jsx';

const FRAMEWORKS = ['ALL', 'GDPR', 'SOX', 'NIST', 'PCI-DSS', 'ISO27001', 'HIPAA'];

const ANOMALY_COLORS = {
  stale_evidence:          '#f59e0b',
  low_confidence_evidence: '#8b5cf6',
  rejected_evidence:       '#ef4444',
  missing_documentation:   '#06b6d4',
  flagged_by_system:       '#ec4899',
  quality_issue:           '#64748b',
  normal:                  '#10b981',
};

const TYPE_LABELS = {
  stale_evidence:          'Stale Evidence',
  low_confidence_evidence: 'Low Confidence',
  rejected_evidence:       'Rejected',
  missing_documentation:   'Missing Docs',
  flagged_by_system:       'Flagged',
  quality_issue:           'Quality Issue',
  normal:                  'Normal',
};

const MetricCard = ({ label, value, icon: Icon, color, sub }) => (
  <motion.div
    whileHover={{ scale: 1.04, y: -6 }}
    className="glass-effect rounded-2xl p-5 border border-white/10 flex flex-col gap-2"
  >
    <div className="flex items-center justify-between">
      <span className="text-gray-400 text-sm">{label}</span>
      <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
    </div>
    <span className="text-3xl font-bold" style={{ color }}>{value}</span>
    {sub && <span className="text-xs text-gray-500">{sub}</span>}
  </motion.div>
);

const AnomalyDetection = () => {
  const [framework, setFramework]       = useState('ALL');
  const [threshold, setThreshold]       = useState(0.20);
  const [running, setRunning]           = useState(false);
  const [evaluating, setEvaluating]     = useState(false);
  const [results, setResults]           = useState(null);
  const [evalResults, setEvalResults]   = useState(null);
  const [activeTab, setActiveTab]       = useState('detect');   // 'detect' | 'evaluate'
  const [summaryData, setSummaryData]   = useState(null);
  const [page, setPage]                 = useState(0);
  const PAGE_SIZE = 25;

  // Load a quick summary on mount
  useEffect(() => {
    anomalyAPI.summary()
      .then(r => setSummaryData(r.data))
      .catch(() => {});
  }, []);

  const runDetection = async () => {
    setRunning(true);
    setResults(null);
    try {
      const res = await anomalyAPI.detect({ threshold, framework: framework === 'ALL' ? null : framework });
      setResults(res.data);
      setPage(0);
    } catch (e) {
      setResults({ error: String(e) });
    } finally {
      setRunning(false);
    }
  };

  const runEvaluation = async () => {
    setEvaluating(true);
    setEvalResults(null);
    try {
      const res = await anomalyAPI.evaluate({});
      setEvalResults(res.data);
    } catch (e) {
      setEvalResults({ error: String(e) });
    } finally {
      setEvaluating(false);
    }
  };

  /* ── helpers ── */
  const typeBreakdownChart = (breakdown) =>
    Object.entries(breakdown || {}).map(([k, v]) => ({
      name: TYPE_LABELS[k] || k,
      value: v,
      fill: ANOMALY_COLORS[k] || '#64748b',
    }));

  const riskColor = (risk) =>
    risk === 'HIGH' ? '#ef4444' : risk === 'MEDIUM' ? '#f59e0b' : '#10b981';

  const anomalyRows = results?.anomalies || [];
  const totalPages  = Math.ceil(anomalyRows.length / PAGE_SIZE);
  const visibleRows = anomalyRows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  /* ── render ── */
  return (
    <div className="min-h-screen p-6 space-y-6">

      {/* ── Header ── */}
      <motion.div
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-red-600 via-orange-600 to-yellow-600"
      >
        <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <motion.div animate={{ rotate: [0, 15, -15, 0] }} transition={{ duration: 2, repeat: Infinity }}>
              <AlertOctagon className="w-10 h-10" />
            </motion.div>
            <div>
              <h1 className="text-4xl font-bold">Anomaly Detection</h1>
              <p className="text-orange-100 mt-1">
                ML-based classifier · Precision &gt; 70% · Recall &gt; 60%
              </p>
            </div>
          </div>

          {/* Quick summary badge */}
          {summaryData && (
            <div className="flex items-center space-x-3 bg-white/10 rounded-2xl px-5 py-3 border border-white/20">
              <div className="text-center">
                <div className="text-2xl font-bold">{summaryData.anomaly_rate}%</div>
                <div className="text-xs text-orange-200">Anomaly Rate</div>
              </div>
              <div className="w-px h-10 bg-white/20" />
              <div className="text-center">
                <div className="text-2xl font-bold" style={{ color: riskColor(summaryData.risk_signal) }}>
                  {summaryData.risk_signal}
                </div>
                <div className="text-xs text-orange-200">Risk Signal</div>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* ── Tabs ── */}
      <div className="flex space-x-2">
        {[
          { id: 'detect',   label: 'Detect Anomalies', icon: Zap },
          { id: 'evaluate', label: 'Evaluate Classifier', icon: Target },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === id
                ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40'
                : 'bg-white/5 text-gray-400 border border-white/10 hover:border-white/20'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* ═══════════════ DETECT TAB ═══════════════ */}
      <AnimatePresence mode="wait">
        {activeTab === 'detect' && (
          <motion.div key="detect" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">

            {/* Controls */}
            <div className="glass-effect rounded-2xl border border-white/10 p-5 flex flex-wrap gap-4 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-400 uppercase tracking-wider">Framework</label>
                <select
                  value={framework}
                  onChange={e => setFramework(e.target.value)}
                  className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 focus:outline-none focus:border-orange-500 text-sm"
                >
                  {FRAMEWORKS.map(f => <option key={f} value={f} className="bg-slate-900">{f}</option>)}
                </select>
              </div>

              <div className="flex flex-col gap-1 flex-1 min-w-48">
                <label className="text-xs text-gray-400 uppercase tracking-wider">
                  Detection Threshold: <span className="text-orange-400 font-bold">{threshold.toFixed(2)}</span>
                </label>
                <input
                  type="range" min="0.20" max="0.80" step="0.05"
                  value={threshold}
                  onChange={e => setThreshold(parseFloat(e.target.value))}
                  className="w-full accent-orange-500"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>0.20 (more detections)</span>
                  <span>0.80 (fewer, high precision)</span>
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={runDetection} disabled={running}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 font-medium hover:bg-orange-500/30 disabled:opacity-50"
              >
                {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                <span>{running ? 'Running…' : 'Run Detection'}</span>
              </motion.button>
            </div>

            {/* Loading */}
            {running && (
              <div className="glass-effect rounded-2xl border border-white/10 p-12 text-center">
                <RefreshCw className="w-10 h-10 animate-spin text-orange-400 mx-auto mb-3" />
                <p className="text-gray-400">Classifying evidence records…</p>
              </div>
            )}

            {/* Error */}
            {results?.error && (
              <div className="glass-effect rounded-2xl border border-red-500/30 p-5 text-red-400">
                Error: {results.error}
              </div>
            )}

            {/* Results */}
            {results && !results.error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">

                {/* Metric cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard label="Total Evidence" value={results.total}
                    icon={BarChart2} color="#3b82f6" sub="records scanned" />
                  <MetricCard label="Anomalies Found" value={results.anomaly_count}
                    icon={AlertTriangle} color="#ef4444" sub={`${results.anomaly_rate}% of total`} />
                  <MetricCard label="Normal Evidence" value={results.normal_count}
                    icon={CheckCircle} color="#10b981" sub="clean records" />
                  <MetricCard label="Threshold Used" value={results.threshold_used?.toFixed(2)}
                    icon={Target} color="#8b5cf6" sub="anomaly cutoff" />
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Bar chart */}
                  <div className="glass-effect rounded-2xl border border-white/10 p-5">
                    <h3 className="text-base font-semibold mb-4 flex items-center space-x-2">
                      <BarChart2 className="w-4 h-4 text-orange-400" />
                      <span>Anomaly Type Breakdown</span>
                    </h3>
                    {typeBreakdownChart(results.anomaly_type_breakdown).length > 0 ? (
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={typeBreakdownChart(results.anomaly_type_breakdown)} layout="vertical">
                          <XAxis type="number" stroke="#64748b" fontSize={11} />
                          <YAxis type="category" dataKey="name" stroke="#64748b" width={110} fontSize={11} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                          />
                          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                            {typeBreakdownChart(results.anomaly_type_breakdown).map((e, i) => (
                              <Cell key={i} fill={e.fill} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-gray-500 text-sm text-center py-8">No anomalies detected</p>
                    )}
                  </div>

                  {/* Pie chart */}
                  <div className="glass-effect rounded-2xl border border-white/10 p-5">
                    <h3 className="text-base font-semibold mb-4 flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-orange-400" />
                      <span>Normal vs Anomalous</span>
                    </h3>
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Normal', value: results.normal_count, fill: '#10b981' },
                            { name: 'Anomalous', value: results.anomaly_count, fill: '#ef4444' },
                          ]}
                          cx="50%" cy="50%"
                          outerRadius={80}
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          dataKey="value"
                        >
                          <Cell fill="#10b981" />
                          <Cell fill="#ef4444" />
                        </Pie>
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Anomaly table */}
                {anomalyRows.length > 0 && (
                  <div className="glass-effect rounded-2xl border border-white/10 overflow-hidden">
                    <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
                      <h3 className="font-semibold flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        <span>Detected Anomalies ({anomalyRows.length})</span>
                      </h3>
                      <div className="flex items-center space-x-2 text-xs text-gray-400">
                        <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                          className="px-2 py-1 rounded bg-white/5 disabled:opacity-30 hover:bg-white/10">‹</button>
                        <span>Page {page + 1} / {totalPages}</span>
                        <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                          className="px-2 py-1 rounded bg-white/5 disabled:opacity-30 hover:bg-white/10">›</button>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-white/10">
                            {['Evidence ID', 'Anomaly Type', 'Score', 'Confidence', 'Freshness', 'Status'].map(h => (
                              <th key={h} className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {visibleRows.map((row, i) => (
                            <motion.tr
                              key={row.evidence_id || i}
                              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                              transition={{ delay: Math.min(i * 0.01, 0.15) }}
                              className="border-b border-white/5 hover:bg-white/5 transition-colors"
                            >
                              <td className="px-4 py-2.5 font-mono text-xs text-orange-300">{row.evidence_id}</td>
                              <td className="px-4 py-2.5">
                                <span className="px-2 py-0.5 rounded-full text-xs border"
                                  style={{
                                    background: `${ANOMALY_COLORS[row.anomaly_type] || '#64748b'}20`,
                                    color: ANOMALY_COLORS[row.anomaly_type] || '#94a3b8',
                                    borderColor: `${ANOMALY_COLORS[row.anomaly_type] || '#64748b'}40`,
                                  }}>
                                  {TYPE_LABELS[row.anomaly_type] || row.anomaly_type}
                                </span>
                              </td>
                              <td className="px-4 py-2.5">
                                <div className="flex items-center space-x-2">
                                  <div className="w-14 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                    <div className="h-full bg-red-500 rounded-full"
                                      style={{ width: `${(row.anomaly_score || 0) * 100}%` }} />
                                  </div>
                                  <span className="text-xs text-gray-400">{((row.anomaly_score || 0) * 100).toFixed(0)}%</span>
                                </div>
                              </td>
                              <td className="px-4 py-2.5 text-xs text-gray-400">
                                {((parseFloat(row.confidence_score) || 0) * 100).toFixed(0)}%
                              </td>
                              <td className="px-4 py-2.5 text-xs">
                                <span className={
                                  parseInt(row.freshness_days) > 90 ? 'text-red-400' :
                                  parseInt(row.freshness_days) > 30 ? 'text-yellow-400' : 'text-green-400'
                                }>{row.freshness_days}d</span>
                              </td>
                              <td className="px-4 py-2.5 text-xs">
                                <span className={
                                  row.status === 'Approved' ? 'text-green-400' :
                                  row.status === 'Rejected' ? 'text-red-400' : 'text-yellow-400'
                                }>{row.status}</span>
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* ═══════════════ EVALUATE TAB ═══════════════ */}
        {activeTab === 'evaluate' && (
          <motion.div key="evaluate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
            <div className="glass-effect rounded-2xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-2 flex items-center space-x-2">
                <Target className="w-5 h-5 text-purple-400" />
                <span>Classifier Self-Evaluation</span>
              </h3>
              <p className="text-gray-400 text-sm mb-5">
                Evaluates the anomaly classifier against the bundled <code className="bg-white/10 px-1 rounded">evidence_labels.csv</code> ground-truth file.
                Targets: <span className="text-yellow-400 font-medium">Precision &gt; 70%</span> and{' '}
                <span className="text-yellow-400 font-medium">Recall &gt; 60%</span>.
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={runEvaluation} disabled={evaluating}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-purple-500/20 border border-purple-500/40 text-purple-300 font-medium hover:bg-purple-500/30 disabled:opacity-50"
              >
                {evaluating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
                <span>{evaluating ? 'Evaluating…' : 'Run Evaluation'}</span>
              </motion.button>
            </div>

            {evaluating && (
              <div className="glass-effect rounded-2xl border border-white/10 p-12 text-center">
                <RefreshCw className="w-10 h-10 animate-spin text-purple-400 mx-auto mb-3" />
                <p className="text-gray-400">Comparing predictions against ground truth…</p>
              </div>
            )}

            {evalResults?.error && (
              <div className="glass-effect rounded-2xl border border-red-500/30 p-5 text-red-400">
                Error: {evalResults.error}
              </div>
            )}

            {evalResults && !evalResults.error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">

                {/* Rubric targets */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    {
                      label: 'Precision',
                      value: `${(evalResults.precision * 100).toFixed(1)}%`,
                      icon: Target,
                      color: evalResults.rubric_targets?.precision_met ? '#10b981' : '#ef4444',
                      sub: evalResults.rubric_targets?.precision_met ? '✅ Target met (>70%)' : '❌ Below target',
                    },
                    {
                      label: 'Recall',
                      value: `${(evalResults.recall * 100).toFixed(1)}%`,
                      icon: TrendingUp,
                      color: evalResults.rubric_targets?.recall_met ? '#10b981' : '#ef4444',
                      sub: evalResults.rubric_targets?.recall_met ? '✅ Target met (>60%)' : '❌ Below target',
                    },
                    {
                      label: 'F1 Score',
                      value: `${(evalResults.f1_score * 100).toFixed(1)}%`,
                      icon: Zap,
                      color: '#8b5cf6',
                      sub: 'Harmonic mean',
                    },
                    {
                      label: 'Accuracy',
                      value: `${(evalResults.accuracy * 100).toFixed(1)}%`,
                      icon: CheckCircle,
                      color: '#3b82f6',
                      sub: `${evalResults.total_samples} samples`,
                    },
                  ].map((card) => (
                    <MetricCard key={card.label} {...card} />
                  ))}
                </div>

                {/* Confusion matrix summary */}
                <div className="glass-effect rounded-2xl border border-white/10 p-6">
                  <h3 className="text-base font-semibold mb-4">Confusion Matrix</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: 'True Positives',  value: evalResults.true_positives,  color: '#10b981', note: 'Correctly flagged' },
                      { label: 'True Negatives',  value: evalResults.true_negatives,  color: '#3b82f6', note: 'Correctly clean' },
                      { label: 'False Positives', value: evalResults.false_positives, color: '#f59e0b', note: 'False alarms' },
                      { label: 'False Negatives', value: evalResults.false_negatives, color: '#ef4444', note: 'Missed anomalies' },
                    ].map(({ label, value, color, note }) => (
                      <div key={label} className="bg-white/5 rounded-xl p-4 text-center border border-white/10">
                        <div className="text-2xl font-bold mb-1" style={{ color }}>{value}</div>
                        <div className="text-xs font-medium text-gray-300">{label}</div>
                        <div className="text-xs text-gray-500 mt-1">{note}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Anomaly counts */}
                <div className="glass-effect rounded-2xl border border-white/10 p-5 flex flex-wrap gap-6 text-sm text-gray-400">
                  <span>Actual anomalies in ground truth: <strong className="text-white">{evalResults.actual_anomalies}</strong></span>
                  <span>Anomalies predicted: <strong className="text-white">{evalResults.anomalies_detected}</strong></span>
                  <span>Total samples compared: <strong className="text-white">{evalResults.total_samples}</strong></span>
                  <span>Evaluated at: <strong className="text-white">{evalResults.evaluated_at?.slice(0, 19)}</strong></span>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AnomalyDetection;
