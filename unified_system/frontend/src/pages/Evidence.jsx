import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Database, Search, CheckCircle, AlertCircle, Clock, XCircle, RefreshCw } from 'lucide-react';
import { evidenceAPI } from '../api/client.jsx';

const Evidence = () => {
  const [evidence, setEvidence] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterFramework, setFilterFramework] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  const frameworks = ['ALL', 'GDPR', 'SOX', 'NIST', 'PCI-DSS', 'ISO27001', 'HIPAA'];
  const statuses = ['ALL', 'Approved', 'Needs_Update', 'Pending_Review', 'Rejected'];

  const load = async () => {
    setLoading(true);
    try {
      const res = await evidenceAPI.getAll();
      const items = res.data?.items || res.data || [];
      setEvidence(items);
      setFiltered(items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    let result = evidence;
    if (filterFramework !== 'ALL') result = result.filter(e => e.framework === filterFramework);
    if (filterStatus !== 'ALL') result = result.filter(e => e.status === filterStatus);
    if (searchTerm) {
      const s = searchTerm.toLowerCase();
      result = result.filter(e =>
        e.evidence_id?.toLowerCase().includes(s) ||
        e.evidence_summary?.toLowerCase().includes(s) ||
        e.evidence_type?.toLowerCase().includes(s) ||
        e.collected_by?.toLowerCase().includes(s)
      );
    }
    setFiltered(result);
  }, [evidence, filterFramework, filterStatus, searchTerm]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Approved': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'Rejected': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'Pending_Review': return <Clock className="w-4 h-4 text-yellow-400" />;
      default: return <AlertCircle className="w-4 h-4 text-orange-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Approved': return 'bg-green-500/10 text-green-400 border-green-500/20';
      case 'Rejected': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'Pending_Review': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      default: return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
    }
  };

  const getFreshnessColor = (days) => {
    if (days <= 7) return 'text-green-400';
    if (days <= 30) return 'text-yellow-400';
    if (days <= 90) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="min-h-screen p-6 space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600">
        <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <Database className="w-10 h-10" />
            <div>
              <h1 className="text-4xl font-bold">Evidence Repository</h1>
              <p className="text-blue-100 mt-1">{filtered.length} of {evidence.length} artifacts shown</p>
            </div>
          </div>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={load} disabled={loading}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-sm font-medium disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Filters */}
      <div className="glass-effect rounded-2xl border border-white/10 p-4 flex flex-wrap gap-4">
        <div className="flex-1 min-w-48 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search evidence..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-white/5 border border-white/10 focus:outline-none focus:border-purple-500 text-sm transition-colors" />
        </div>
        <select value={filterFramework} onChange={e => setFilterFramework(e.target.value)}
          className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 focus:outline-none focus:border-purple-500 text-sm">
          {frameworks.map(f => <option key={f} value={f} className="bg-slate-900">{f}</option>)}
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 focus:outline-none focus:border-purple-500 text-sm">
          {statuses.map(s => <option key={s} value={s} className="bg-slate-900">{s}</option>)}
        </select>
      </div>

      <div className="glass-effect rounded-2xl border border-white/10 overflow-hidden">
        {loading ? (
          <div className="p-16 text-center">
            <RefreshCw className="w-10 h-10 animate-spin text-purple-400 mx-auto mb-4" />
            <p className="text-gray-400">Loading evidence...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-16 text-center">
            <Database className="w-12 h-12 mx-auto mb-4 text-gray-600" />
            <p className="text-gray-500">No evidence found. Initialize the system first.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  {['Evidence ID','Framework','Type','Collected By','Freshness','Status','Confidence'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((ev, i) => (
                  <motion.tr key={ev.evidence_id || i}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: Math.min(i * 0.005, 0.2) }}
                    onClick={() => setSelectedEvidence(ev)}
                    className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs text-purple-300">{ev.evidence_id}</td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded text-xs bg-blue-500/10 text-blue-300 border border-blue-500/20">{ev.framework}</span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-300 text-xs">{ev.evidence_type}</td>
                    <td className="px-4 py-2.5 text-gray-400 text-xs">{ev.collected_by}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-xs font-medium ${getFreshnessColor(ev.freshness_days)}`}>{ev.freshness_days}d</span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded-full text-xs border flex items-center space-x-1 w-fit ${getStatusColor(ev.status)}`}>
                        {getStatusIcon(ev.status)}<span>{ev.status?.replace('_', ' ')}</span>
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center space-x-2">
                        <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div className="h-full bg-purple-500 rounded-full" style={{ width: `${(ev.confidence_score || 0) * 100}%` }} />
                        </div>
                        <span className="text-xs text-gray-400">{((ev.confidence_score || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedEvidence && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="glass-effect rounded-2xl border border-purple-500/30 p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-purple-300">{selectedEvidence.evidence_id}</h3>
            <button onClick={() => setSelectedEvidence(null)} className="text-gray-400 hover:text-white text-xl leading-none">×</button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-4">
            {[
              ['Framework', selectedEvidence.framework],
              ['Type', selectedEvidence.evidence_type],
              ['Status', selectedEvidence.status],
              ['Freshness', `${selectedEvidence.freshness_days} days`],
              ['Collected By', selectedEvidence.collected_by],
              ['Collection Date', selectedEvidence.collection_date],
              ['Confidence', `${((selectedEvidence.confidence_score || 0) * 100).toFixed(0)}%`],
              ['Location', selectedEvidence.evidence_location],
            ].map(([k, v]) => (
              <div key={k} className="bg-white/5 rounded-lg p-3">
                <div className="text-gray-500 text-xs mb-1">{k}</div>
                <div className="text-gray-200 truncate">{v || '—'}</div>
              </div>
            ))}
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-gray-500 text-xs mb-1">Summary</div>
            <div className="text-gray-300 text-sm">{selectedEvidence.evidence_summary || '—'}</div>
          </div>
          {selectedEvidence.anomaly_marker && (
            <div className="mt-3 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
              ⚠ Anomaly: {selectedEvidence.anomaly_marker}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Evidence;

