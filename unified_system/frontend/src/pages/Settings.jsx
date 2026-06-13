import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Database, RefreshCw, CheckCircle, AlertTriangle, Zap, Upload } from 'lucide-react';
import { initAPI, healthAPI, mappingsAPI } from '../api/client.jsx';

const PIPELINE_STEPS = [
  { name: 'Frontend UI', desc: 'React 18 · Framer Motion · Tailwind', status: 'active', color: '#3b82f6' },
  { name: 'Compliance Copilot', desc: 'Natural language query interface', status: 'active', color: '#8b5cf6' },
  { name: 'LLM Requirement Extractor', desc: 'Policy → structured requirements', status: 'active', color: '#ec4899' },
  { name: 'Semantic Mapper', desc: 'Evidence ↔ requirement matching', status: 'active', color: '#10b981' },
  { name: 'Knowledge Graph', desc: 'NetworkX relationship graph', status: 'active', color: '#f59e0b' },
  { name: 'Challenge Auditor', desc: 'Adversarial compliance stress-testing', status: 'active', color: '#f97316' },
  { name: 'Confidence Engine', desc: 'Multi-factor confidence scoring', status: 'active', color: '#06b6d4' },
  { name: 'Narrative Generator', desc: 'AI-generated audit narratives', status: 'active', color: '#84cc16' },
  { name: 'Report', desc: 'Comprehensive audit-ready reports', status: 'active', color: '#a78bfa' },
];

const Settings = () => {
  const [apiHealth, setApiHealth] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [rebuildLoading, setRebuildLoading] = useState(false);
  const [initResult, setInitResult] = useState(null);
  const [policyText, setPolicyText] = useState('');
  const [useCustomPolicy, setUseCustomPolicy] = useState(false);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const [hRes, sRes] = await Promise.all([healthAPI.check(), healthAPI.status()]);
      setApiHealth(hRes.data);
      setSystemStatus(sRes.data);
    } catch (e) {
      setApiHealth({ healthy: false, error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  const initSystem = async () => {
    setInitLoading(true);
    setInitResult(null);
    try {
      const res = await initAPI.initialize({});
      setInitResult({ success: true, data: res.data });
    } catch (e) {
      setInitResult({ success: false, error: String(e) });
    } finally {
      setInitLoading(false);
    }
  };

  const rebuildMappings = async () => {
    setRebuildLoading(true);
    try {
      await mappingsAPI.rebuild();
    } catch (e) {
      console.error(e);
    } finally {
      setRebuildLoading(false);
    }
  };

  useEffect(() => { checkHealth(); }, []);

  const StatusDot = ({ ok }) => (
    <div className={`w-2.5 h-2.5 rounded-full ${ok ? 'bg-green-400' : 'bg-red-400'} animate-pulse`} />
  );

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-slate-700 via-gray-700 to-slate-800"
      >
        <div className="relative z-10 flex items-center space-x-4">
          <motion.div animate={{ rotate: [0, 180, 360] }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}>
            <SettingsIcon className="w-10 h-10 text-gray-300" />
          </motion.div>
          <div>
            <h1 className="text-4xl font-bold">System Settings</h1>
            <p className="text-gray-400 mt-1">Initialize, configure, and monitor the compliance platform</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <div className="glass-effect rounded-2xl border border-white/10 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              <span>System Health</span>
            </h3>
            <motion.button
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={checkHealth} disabled={loading}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-sm text-gray-300 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </motion.button>
          </div>

          {apiHealth && (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <span className="text-sm text-gray-300">API Backend</span>
                <div className="flex items-center space-x-2">
                  <StatusDot ok={apiHealth.healthy} />
                  <span className={`text-xs font-medium ${apiHealth.healthy ? 'text-green-400' : 'text-red-400'}`}>
                    {apiHealth.healthy ? 'Healthy' : 'Offline'}
                  </span>
                </div>
              </div>

              {systemStatus && (
                <>
                  {[
                    ['Total Evidence', systemStatus.totalEvidence],
                    ['Total Requirements', systemStatus.totalRequirements],
                    ['Total Mappings', systemStatus.totalMappings],
                    ['Critical Findings', systemStatus.criticalFindings],
                  ].map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                      <span className="text-sm text-gray-400">{k}</span>
                      <span className="text-sm font-semibold text-white">{v ?? '—'}</span>
                    </div>
                  ))}

                  {systemStatus.components && (
                    <div className="mt-3">
                      <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Components</div>
                      {Object.entries(systemStatus.components).map(([comp, status]) => (
                        <div key={comp} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                          <span className="text-xs text-gray-400">{comp.replace(/_/g, ' ')}</span>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            status === 'active' || status === 'mock' || status === 'live'
                              ? 'bg-green-500/10 text-green-400'
                              : 'bg-yellow-500/10 text-yellow-400'
                          }`}>{status}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* Initialize */}
        <div className="glass-effect rounded-2xl border border-white/10 p-6 space-y-4">
          <h3 className="text-lg font-semibold flex items-center space-x-2">
            <Database className="w-5 h-5 text-blue-400" />
            <span>Initialize System</span>
          </h3>
          <p className="text-sm text-gray-400">
            Loads the default policy documents and evidence CSV, extracts requirements,
            builds the knowledge graph, and runs semantic mapping.
          </p>

          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={initSystem} disabled={initLoading}
            className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-medium disabled:opacity-50 transition-all"
          >
            {initLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
            <span>{initLoading ? 'Initializing...' : 'Initialize with Default Data'}</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={rebuildMappings} disabled={rebuildLoading}
            className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-sm font-medium disabled:opacity-50 transition-all border border-white/10"
          >
            <RefreshCw className={`w-4 h-4 ${rebuildLoading ? 'animate-spin' : ''}`} />
            <span>{rebuildLoading ? 'Rebuilding...' : 'Rebuild Semantic Mappings'}</span>
          </motion.button>

          {initResult && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border ${initResult.success
                ? 'bg-green-500/10 border-green-500/20'
                : 'bg-red-500/10 border-red-500/20'
              }`}>
              {initResult.success ? (
                <div className="space-y-1 text-sm">
                  <div className="flex items-center space-x-2 text-green-400 font-semibold">
                    <CheckCircle className="w-4 h-4" />
                    <span>Initialization Successful</span>
                  </div>
                  {[
                    ['Policies Loaded', initResult.data?.policies_loaded],
                    ['Requirements Extracted', initResult.data?.requirements_extracted],
                    ['Evidence Loaded', initResult.data?.evidence_loaded],
                    ['Mappings Created', initResult.data?.mappings_created],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between text-gray-300 py-0.5">
                      <span>{k}</span>
                      <span className="font-semibold text-green-300">{v ?? 0}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-start space-x-2 text-red-400 text-sm">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{initResult.error}</span>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>

      {/* Pipeline Visualization */}
      <div className="glass-effect rounded-2xl border border-white/10 p-6">
        <h3 className="text-lg font-semibold mb-5 flex items-center space-x-2">
          <Zap className="w-5 h-5 text-purple-400" />
          <span>Full Pipeline Architecture</span>
        </h3>
        <div className="flex flex-wrap items-center gap-2">
          {PIPELINE_STEPS.map((step, i) => (
            <React.Fragment key={step.name}>
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.07 }}
                className="group relative flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all min-w-28 text-center cursor-default"
                style={{ borderColor: `${step.color}30` }}
              >
                <div className="w-2.5 h-2.5 rounded-full mb-2 animate-pulse" style={{ backgroundColor: step.color }} />
                <span className="text-xs font-semibold text-gray-200 leading-tight">{step.name}</span>
                <span className="text-xs text-gray-500 mt-0.5 leading-tight">{step.desc}</span>
              </motion.div>
              {i < PIPELINE_STEPS.length - 1 && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.07 + 0.05 }}
                  className="text-gray-600 text-lg hidden sm:block"
                >↓</motion.div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="glass-effect rounded-2xl border border-white/10 p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Start</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          {[
            {
              step: '1', title: 'Initialize System',
              desc: 'Click "Initialize with Default Data" above to load policies, extract requirements, and map evidence.',
              color: '#3b82f6',
            },
            {
              step: '2', title: 'Explore & Analyse',
              desc: 'Use Analysis, Challenge Audit, and Confidence pages to score your compliance posture.',
              color: '#8b5cf6',
            },
            {
              step: '3', title: 'Ask the Copilot',
              desc: 'Use the Copilot page to query compliance status in plain English and get AI-powered answers.',
              color: '#10b981',
            },
          ].map(s => (
            <div key={s.step} className="bg-white/5 rounded-xl p-4 border border-white/5">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold mb-3"
                style={{ backgroundColor: `${s.color}40`, border: `1px solid ${s.color}60` }}>
                {s.step}
              </div>
              <div className="font-semibold text-gray-200 mb-1">{s.title}</div>
              <div className="text-gray-400 text-xs leading-relaxed">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Settings;

