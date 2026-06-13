import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Zap, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { challengeAPI } from '../api/client.jsx';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'bg-red-500/10 border-red-500/20', icon: XCircle, label: '🔴 CRITICAL' },
  HIGH:     { color: '#f97316', bg: 'bg-orange-500/10 border-orange-500/20', icon: AlertTriangle, label: '🟠 HIGH' },
  MEDIUM:   { color: '#f59e0b', bg: 'bg-amber-500/10 border-amber-500/20', icon: AlertCircle, label: '🟡 MEDIUM' },
  LOW:      { color: '#10b981', bg: 'bg-emerald-500/10 border-emerald-500/20', icon: CheckCircle, label: '🟢 LOW' },
};

const STATUS_CONFIG = {
  PASS:              { color: '#10b981', label: '✅ PASS' },
  PASS_WITH_CONCERNS:{ color: '#f59e0b', label: '⚡ PASS WITH CONCERNS' },
  CONDITIONAL_PASS:  { color: '#f97316', label: '⚠️ CONDITIONAL PASS' },
  FAIL:              { color: '#ef4444', label: '❌ FAIL' },
};

const FRAMEWORKS = ['ALL', 'GDPR', 'SOX', 'NIST', 'PCI-DSS', 'ISO27001', 'HIPAA'];

const FindingCard = ({ finding, index }) => {
  const cfg = SEVERITY_CONFIG[finding.severity] || SEVERITY_CONFIG.LOW;
  const Icon = cfg.icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className={`rounded-xl border p-4 ${cfg.bg}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start space-x-3 flex-1">
          <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: cfg.color }} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center flex-wrap gap-2 mb-1">
              <span className="font-mono text-xs text-gray-400">{finding.requirement}</span>
              <span className="text-xs font-bold" style={{ color: cfg.color }}>{cfg.label}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400">
                {finding.title}
              </span>
            </div>
            <p className="text-sm text-gray-300">{finding.description}</p>
            <p className="text-xs text-gray-500 mt-1.5">
              <span className="text-blue-400 font-medium">Remediation: </span>
              {finding.remediation}
            </p>
          </div>
        </div>
        <span className="text-xs px-2 py-1 rounded-lg bg-white/5 text-gray-400 flex-shrink-0">
          {STATUS_CONFIG[finding.status]?.label || finding.status}
        </span>
      </div>
    </motion.div>
  );
};

const ChallengeAudit = () => {
  const [selectedFramework, setSelectedFramework] = useState('GDPR');
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);

  const runChallengeAudit = async () => {
    setIsRunning(true);
    setProgress(0);
    setResults(null);

    // Animate progress bar while API call runs
    const timer = setInterval(() => {
      setProgress(prev => (prev < 88 ? prev + 4 : prev));
    }, 180);

    try {
      const res = await challengeAPI.run(selectedFramework);
      const data = res.data;
      clearInterval(timer);
      setProgress(100);

      const findings = (data.detailed_results || []).flatMap((r, ri) =>
        (r.findings || []).map((f, fi) => ({
          id: `${ri}-${fi}`,
          requirement: r.requirement_id,
          title: (f.type || '').replace(/_/g, ' '),
          severity: f.severity || 'LOW',
          description: f.description || '',
          remediation: f.remediation || '',
          status: r.status,
        }))
      );

      setResults({
        totalChallenged: data.total_challenged || 0,
        pass: data.pass_count || 0,
        passWithConcerns: data.concerns_count || 0,
        conditionalPass: data.conditional_count || 0,
        fail: data.fail_count || 0,
        criticalFindings: data.critical_findings || 0,
        highFindings: data.high_findings || 0,
        totalFindings: data.total_findings || 0,
        executiveSummary: data.executive_summary || '',
        findings,
      });
    } catch (e) {
      clearInterval(timer);
      console.error('Challenge audit error:', e);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-red-600 via-orange-600 to-amber-600"
      >
        <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 2, repeat: Infinity }}>
              <Zap className="w-10 h-10 text-yellow-300" />
            </motion.div>
            <div>
              <h1 className="text-4xl font-bold">Challenge Auditor</h1>
              <p className="text-orange-100 mt-1">Adversarial stress-testing — find weaknesses before auditors do</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={selectedFramework}
              onChange={e => setSelectedFramework(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/20 border border-white/20 focus:outline-none text-sm font-medium"
            >
              {FRAMEWORKS.map(f => <option key={f} value={f} className="bg-slate-900">{f}</option>)}
            </select>
            <motion.button
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={runChallengeAudit} disabled={isRunning}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 font-medium disabled:opacity-50"
            >
              {isRunning ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
              <span>{isRunning ? 'Challenging...' : 'Run Challenge Audit'}</span>
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Progress bar */}
      {isRunning && (
        <div className="glass-effect rounded-2xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-300">Running adversarial audit for <strong>{selectedFramework}</strong>…</span>
            <span className="text-sm text-orange-400 font-bold">{progress}%</span>
          </div>
          <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-orange-500 to-red-500"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}

      {/* Placeholder */}
      {!results && !isRunning && (
        <div className="glass-effect rounded-2xl border border-white/10 p-16 text-center">
          <Zap className="w-16 h-16 text-orange-400 mx-auto mb-4 opacity-40" />
          <h3 className="text-xl font-semibold text-gray-300 mb-2">Devil's Advocate Mode</h3>
          <p className="text-gray-500 max-w-lg mx-auto">
            The Challenge Auditor simulates a strict external auditor who stress-tests every
            requirement's evidence — checking freshness, scope, conflicts, documentation
            completeness, and confidence levels.
          </p>
        </div>
      )}

      {/* Results */}
      {results && !isRunning && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Challenged', value: results.totalChallenged, color: '#8b5cf6' },
              { label: '✅ Pass', value: results.pass, color: '#10b981' },
              { label: '⚠️ Conditional', value: results.conditionalPass, color: '#f97316' },
              { label: '❌ Fail', value: results.fail, color: '#ef4444' },
            ].map(s => (
              <div key={s.label} className="glass-effect rounded-xl border border-white/10 p-4 text-center">
                <div className="text-3xl font-bold" style={{ color: s.color }}>{s.value}</div>
                <div className="text-xs text-gray-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Finding severity breakdown */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: '🔴 Critical', value: results.criticalFindings, color: '#ef4444' },
              { label: '🟠 High', value: results.highFindings, color: '#f97316' },
              { label: '📊 Total Findings', value: results.totalFindings, color: '#8b5cf6' },
            ].map(s => (
              <div key={s.label} className="glass-effect rounded-xl border border-white/10 p-4 text-center">
                <div className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</div>
                <div className="text-xs text-gray-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Executive summary */}
          {results.executiveSummary && (
            <div className="glass-effect rounded-2xl border border-orange-500/20 p-5">
              <h3 className="text-sm font-semibold text-orange-400 uppercase tracking-wider mb-2">Executive Summary</h3>
              <p className="text-gray-200">{results.executiveSummary}</p>
            </div>
          )}

          {/* Findings list */}
          {results.findings.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-300">
                All Findings ({results.findings.length})
              </h3>
              {results.findings.map((f, i) => (
                <FindingCard key={f.id} finding={f} index={i} />
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default ChallengeAudit;

