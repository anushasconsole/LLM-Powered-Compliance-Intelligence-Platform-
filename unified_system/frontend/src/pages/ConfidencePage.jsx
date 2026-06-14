import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, RefreshCw, CheckCircle, AlertTriangle, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { analysisAPI } from '../api/client.jsx';

const STATUS_CONFIG = {
  COMPLIANT: { color: '#10b981', bg: 'bg-emerald-500/10', icon: CheckCircle, label: 'Compliant', border: 'border-emerald-500/30' },
  CONDITIONAL: { color: '#f59e0b', bg: 'bg-amber-500/10', icon: AlertTriangle, label: 'Conditional', border: 'border-amber-500/30' },
  AT_RISK: { color: '#f97316', bg: 'bg-orange-500/10', icon: AlertTriangle, label: 'At Risk', border: 'border-orange-500/30' },
  NON_COMPLIANT: { color: '#ef4444', bg: 'bg-red-500/10', icon: XCircle, label: 'Non-Compliant', border: 'border-red-500/30' },
};

const FactorBar = ({ factor }) => (
  <div className="space-y-1">
    <div className="flex justify-between text-xs text-gray-400">
      <span>{factor.name}</span>
      <span className="font-medium text-white">{(factor.score * 100).toFixed(0)}%</span>
    </div>
    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${factor.score * 100}%` }}
        transition={{ duration: 0.8 }}
        className="h-full rounded-full"
        style={{
          background: factor.score >= 0.7 ? '#10b981' : factor.score >= 0.5 ? '#f59e0b' : '#ef4444'
        }}
      />
    </div>
    <div className="text-xs text-gray-500">{factor.reasoning}</div>
  </div>
);

const RequirementCard = ({ req }) => {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[req.compliance_status] || STATUS_CONFIG.NON_COMPLIANT;
  const StatusIcon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-effect rounded-xl border ${cfg.border} p-5`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <StatusIcon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: cfg.color }} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <span className="text-xs font-mono text-gray-400">{req.requirement_id}</span>
              <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: `${cfg.color}20`, color: cfg.color }}>
                {cfg.label}
              </span>
              {req.audit_ready && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
                  Audit Ready ✓
                </span>
              )}
            </div>
            <p className="text-sm text-gray-200 mt-1 line-clamp-2">{req.description}</p>
          </div>
        </div>
        <div className="text-right ml-4 flex-shrink-0">
          <div className="text-2xl font-bold" style={{ color: cfg.color }}>
            {req.confidence_percentage}
          </div>
          <div className="text-xs text-gray-500">confidence</div>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: req.confidence_percentage }}
          transition={{ duration: 1 }}
          className="h-full rounded-full"
          style={{ backgroundColor: cfg.color }}
        />
      </div>

      {/* Toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-3 text-xs text-gray-400 hover:text-white flex items-center space-x-1 transition-colors"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        <span>{expanded ? 'Less detail' : 'Show detail'}</span>
      </button>

      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-4 space-y-4 border-t border-white/5 pt-4"
        >
          {/* Factors */}
          {req.factors && req.factors.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-300 mb-3 uppercase tracking-wider">Confidence Factors</h4>
              <div className="space-y-3">
                {req.factors.map((f, i) => <FactorBar key={i} factor={f} />)}
              </div>
            </div>
          )}

          {/* Narrative */}
          {req.narrative && (
            <div>
              <h4 className="text-xs font-semibold text-gray-300 mb-2 uppercase tracking-wider">Narrative</h4>
              <p className="text-xs text-gray-400 leading-relaxed">{req.narrative.executive_summary}</p>
              {req.narrative.risk_assessment && (
                <p className="mt-2 text-xs text-gray-500">{req.narrative.risk_assessment}</p>
              )}
            </div>
          )}

          {/* Red flags / strengths */}
          {req.red_flags && req.red_flags.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-red-400 mb-2 uppercase tracking-wider">⚠ Red Flags</h4>
              {req.red_flags.map((f, i) => (
                <div key={i} className="text-xs text-red-300 flex items-start space-x-1.5 mb-1">
                  <span>•</span><span>{f}</span>
                </div>
              ))}
            </div>
          )}

          {req.strengths && req.strengths.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-green-400 mb-2 uppercase tracking-wider">✓ Strengths</h4>
              {req.strengths.map((s, i) => (
                <div key={i} className="text-xs text-green-300 flex items-start space-x-1.5 mb-1">
                  <span>•</span><span>{s}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>Next review: {req.next_review_date}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

const FRAMEWORKS = ['ALL', 'GDPR', 'SOX', 'NIST', 'PCI-DSS', 'ISO27001', 'HIPAA'];

const ConfidencePage = () => {
  const [framework, setFramework] = useState('ALL');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const res = await analysisAPI.confidence(framework);
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-amber-600 via-orange-600 to-red-600"
      >
        <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <Zap className="w-10 h-10 text-yellow-300" />
            <div>
              <h1 className="text-4xl font-bold">Confidence Engine</h1>
              <p className="text-orange-100 mt-1">Multi-factor auditor confidence scoring with AI narratives</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={framework}
              onChange={e => setFramework(e.target.value)}
              className="glass-effect px-4 py-2 rounded-xl border border-white/20 focus:outline-none focus:border-white/40 bg-transparent text-sm"
            >
              {FRAMEWORKS.map(fw => <option key={fw} value={fw} className="bg-slate-900">{fw}</option>)}
            </select>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={run}
              disabled={loading}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 transition-colors disabled:opacity-50 text-sm font-medium"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Run Assessment</span>
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Summary */}
      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Compliant', value: data.compliant, color: '#10b981' },
            { label: 'Conditional', value: data.conditional, color: '#f59e0b' },
            { label: 'At Risk', value: data.at_risk, color: '#f97316' },
            { label: 'Non-Compliant', value: data.non_compliant, color: '#ef4444' },
          ].map(s => (
            <div key={s.label} className="glass-effect rounded-xl border border-white/10 p-4 text-center">
              <div className="text-3xl font-bold" style={{ color: s.color }}>{s.value}</div>
              <div className="text-sm text-gray-400 mt-1">{s.label}</div>
            </div>
          ))}
        </motion.div>
      )}

      {/* Requirements list */}
      {data ? (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-300">
            Requirements Assessment — {data.framework} ({data.total_requirements} total)
          </h2>
          {data.requirements.map((req, i) => (
            <RequirementCard key={req.requirement_id || i} req={req} />
          ))}
        </div>
      ) : (
        <div className="glass-effect rounded-2xl border border-white/10 p-16 text-center">
          <Zap className="w-16 h-16 text-amber-400 mx-auto mb-4 opacity-50" />
          <h3 className="text-xl font-semibold text-gray-300 mb-2">Run Confidence Assessment</h3>
          <p className="text-gray-500 max-w-md mx-auto">
            Select a framework and click "Run Assessment" to calculate multi-factor confidence scores
            with AI-generated audit narratives for each requirement.
          </p>
        </div>
      )}
    </div>
  );
};

export default ConfidencePage;

