import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, RefreshCw, Plus, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { reportsAPI } from '../api/client.jsx';

const STATUS_COLORS = {
  COMPLIANT: 'text-green-400 bg-green-500/10 border-green-500/20',
  NON_COMPLIANT: 'text-red-400 bg-red-500/10 border-red-500/20',
  PARTIAL: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  UNKNOWN: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
};

const FRAMEWORKS = ['ALL', 'GDPR', 'SOX', 'NIST', 'PCI-DSS', 'ISO27001', 'HIPAA'];

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [genFramework, setGenFramework] = useState('ALL');

  const loadReports = async () => {
    setLoading(true);
    try {
      const res = await reportsAPI.getAll();
      setReports(res.data?.items || res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    try {
      const res = await reportsAPI.generate(genFramework);
      setSelectedReport(res.data);
      await loadReports();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const downloadJSON = (report) => {
    const data = JSON.stringify(report, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${report.report_id || 'compliance-report'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => { loadReports(); }, []);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-600">
        <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <FileText className="w-10 h-10" />
            <div>
              <h1 className="text-4xl font-bold">Compliance Reports</h1>
              <p className="text-indigo-100 mt-1">Audit-ready comprehensive reports</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <select value={genFramework} onChange={e => setGenFramework(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/20 border border-white/20 focus:outline-none text-sm">
              {FRAMEWORKS.map(fw => <option key={fw} value={fw} className="bg-slate-900">{fw}</option>)}
            </select>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={generateReport} disabled={generating}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-sm font-medium disabled:opacity-50">
              <Plus className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
              <span>{generating ? 'Generating...' : 'Generate Report'}</span>
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={loadReports} disabled={loading}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-sm disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </motion.button>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reports list */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-300">Generated Reports ({reports.length})</h2>
          {reports.length === 0 ? (
            <div className="glass-effect rounded-2xl border border-white/10 p-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-500">No reports yet. Generate one above.</p>
            </div>
          ) : (
            reports.map((r, i) => (
              <motion.div key={r.report_id || i}
                initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => setSelectedReport(r)}
                className={`glass-effect rounded-xl border p-4 cursor-pointer transition-all hover:border-white/20 ${
                  selectedReport?.report_id === r.report_id ? 'border-purple-500/50' : 'border-white/10'
                }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-mono text-xs text-purple-300 mb-1">{r.report_id}</div>
                    <div className="font-medium text-sm">{r.framework} — {r.report_type}</div>
                    <div className="text-xs text-gray-500 mt-1">{new Date(r.generated_at || r.created_at).toLocaleString()}</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs border ${STATUS_COLORS[r.status] || STATUS_COLORS.UNKNOWN}`}>
                      {r.status}
                    </span>
                    <button onClick={e => { e.stopPropagation(); downloadJSON(r); }}
                      className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                {r.summary && <p className="text-xs text-gray-400 mt-2 line-clamp-2">{r.summary}</p>}
              </motion.div>
            ))
          )}
        </div>

        {/* Report detail */}
        <div>
          {selectedReport ? (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
              className="glass-effect rounded-2xl border border-white/10 p-6 space-y-5 sticky top-20">
              <div className="flex justify-between items-start">
                <h3 className="font-semibold text-purple-300">{selectedReport.report_id}</h3>
                <button onClick={() => downloadJSON(selectedReport)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 text-xs transition-colors">
                  <Download className="w-3 h-3" /><span>Download JSON</span>
                </button>
              </div>

              {selectedReport.executive_summary && (
                <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Executive Summary</div>
                  <p className="text-sm text-gray-200">{selectedReport.executive_summary}</p>
                </div>
              )}

              {selectedReport.compliance_analysis && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Compliance Analysis</div>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      ['Score', `${selectedReport.compliance_analysis.compliance_score}%`],
                      ['Coverage', selectedReport.compliance_analysis.coverage_percentage],
                      ['Requirements', selectedReport.compliance_analysis.requirements_analyzed],
                      ['Gaps', selectedReport.compliance_analysis.requirements_with_gaps],
                    ].map(([k, v]) => (
                      <div key={k} className="bg-white/5 rounded-lg p-3 text-center">
                        <div className="text-lg font-bold text-purple-300">{v}</div>
                        <div className="text-xs text-gray-500">{k}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedReport.recommendations && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Recommendations</div>
                  <div className="space-y-2">
                    {selectedReport.recommendations.map((r, i) => (
                      <div key={i} className="flex items-start space-x-2 text-sm text-gray-300">
                        <div className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-2 flex-shrink-0" />
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ) : (
            <div className="glass-effect rounded-2xl border border-white/10 p-12 text-center sticky top-20">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-500">Select a report to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Reports;

