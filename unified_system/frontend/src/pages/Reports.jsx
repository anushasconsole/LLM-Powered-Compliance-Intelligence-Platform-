import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText, Download, RefreshCw, Plus, AlertTriangle,
  FileJson, FileCode, Eye, CheckCircle, XCircle, Loader,
} from 'lucide-react';
import { reportsAPI } from '../api/client.jsx';

const STATUS_COLORS = {
  COMPLIANT:     'text-green-400 bg-green-500/10 border-green-500/20',
  NON_COMPLIANT: 'text-red-400 bg-red-500/10 border-red-500/20',
  PARTIAL:       'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  UNKNOWN:       'text-gray-400 bg-gray-500/10 border-gray-500/20',
};

const FRAMEWORKS = ['ALL', 'GDPR', 'SOX', 'NIST', 'PCI-DSS', 'ISO27001', 'HIPAA'];

/* ─── helpers ─────────────────────────────────────────────────────────── */

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href     = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ─── component ───────────────────────────────────────────────────────── */

const Reports = () => {
  const [reports, setReports]           = useState([]);
  const [loading, setLoading]           = useState(false);
  const [generating, setGenerating]     = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [genFramework, setGenFramework] = useState('ALL');
  const [downloading, setDownloading]   = useState({});   // { reportId: 'pdf'|'json'|null }
  const [previewHtml, setPreviewHtml]   = useState(null); // for inline HTML preview
  const [previewOpen, setPreviewOpen]   = useState(false);

  /* ── data loading ── */
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

  useEffect(() => { loadReports(); }, []);

  /* ── download: JSON ── */
  const downloadJSON = (report) => {
    const id = report.report_id || 'compliance-report';
    setDownloading(prev => ({ ...prev, [id]: 'json' }));
    try {
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      downloadBlob(blob, `${id}.json`);
    } finally {
      setDownloading(prev => ({ ...prev, [id]: null }));
    }
  };

  /* ── download: PDF/HTML (backend renders the HTML report) ── */
  const downloadPDF = async (report) => {
    const id = report.report_id;
    if (!id) return;
    setDownloading(prev => ({ ...prev, [id]: 'pdf' }));
    try {
      const res = await reportsAPI.downloadPdf(id);
      // Backend returns HTML (or PDF if weasyprint/reportlab installed)
      const contentType = res.headers?.['content-type'] || 'text/html';
      const isPdf = contentType.includes('pdf');
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: contentType });
      downloadBlob(blob, `${id}.${isPdf ? 'pdf' : 'html'}`);
    } catch (e) {
      console.error('PDF download failed:', e);
    } finally {
      setDownloading(prev => ({ ...prev, [id]: null }));
    }
  };

  /* ── preview: open HTML report in an inline modal iframe ── */
  const previewReport = async (report) => {
    const id = report.report_id;
    if (!id) return;
    setDownloading(prev => ({ ...prev, [id]: 'preview' }));
    try {
      const res = await reportsAPI.downloadPdf(id);
      const contentType = res.headers?.['content-type'] || 'text/html';
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: contentType });
      const url  = URL.createObjectURL(blob);
      setPreviewHtml(url);
      setPreviewOpen(true);
    } catch (e) {
      console.error('Preview failed:', e);
    } finally {
      setDownloading(prev => ({ ...prev, [id]: null }));
    }
  };

  const closePreview = () => {
    if (previewHtml) URL.revokeObjectURL(previewHtml);
    setPreviewHtml(null);
    setPreviewOpen(false);
  };

  /* ── render ── */
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
              <p className="text-indigo-100 mt-1">Audit-ready reports · JSON &amp; PDF/HTML download</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <select value={genFramework} onChange={e => setGenFramework(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/20 border border-white/20 focus:outline-none text-sm">
              {FRAMEWORKS.map(fw => (
                <option key={fw} value={fw} className="bg-slate-900">{fw}</option>
              ))}
            </select>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={generateReport} disabled={generating}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-sm font-medium disabled:opacity-50">
              {generating
                ? <Loader className="w-4 h-4 animate-spin" />
                : <Plus className="w-4 h-4" />}
              <span>{generating ? 'Generating…' : 'Generate Report'}</span>
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={loadReports} disabled={loading}
              className="p-2.5 rounded-xl bg-white/20 hover:bg-white/30 disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Download format note */}
      <div className="flex items-start space-x-3 px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-sm text-blue-300">
        <FileCode className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span>
          PDF download generates an <strong>HTML report</strong> if <code>weasyprint</code>/<code>reportlab</code> are not
          installed, or a true PDF when they are. Install with:&nbsp;
          <code className="bg-white/10 px-1 rounded">pip install weasyprint</code>&nbsp;or&nbsp;
          <code className="bg-white/10 px-1 rounded">pip install reportlab</code>
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ── Reports list ── */}
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-300">
            Generated Reports ({reports.length})
          </h2>

          {reports.length === 0 ? (
            <div className="glass-effect rounded-2xl border border-white/10 p-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-500">No reports yet. Generate one above.</p>
            </div>
          ) : (
            reports.map((r, i) => {
              const rid  = r.report_id || String(i);
              const busy = downloading[rid];
              return (
                <motion.div key={rid}
                  initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  onClick={() => setSelectedReport(r)}
                  className={`glass-effect rounded-xl border p-4 cursor-pointer transition-all hover:border-white/20 ${
                    selectedReport?.report_id === rid ? 'border-purple-500/50' : 'border-white/10'
                  }`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="font-mono text-xs text-purple-300 mb-1 truncate">{rid}</div>
                      <div className="font-medium text-sm">{r.framework} — {r.report_type}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(r.generated_at || r.created_at).toLocaleString()}
                      </div>
                    </div>

                    <div className="flex items-center space-x-1.5 flex-shrink-0">
                      <span className={`px-2 py-0.5 rounded-full text-xs border ${STATUS_COLORS[r.status] || STATUS_COLORS.UNKNOWN}`}>
                        {r.status}
                      </span>

                      {/* Preview button */}
                      <button
                        title="Preview HTML report"
                        onClick={e => { e.stopPropagation(); previewReport(r); }}
                        disabled={!!busy}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-blue-500/20 text-gray-400 hover:text-blue-300 transition-colors disabled:opacity-40">
                        {busy === 'preview'
                          ? <Loader className="w-3.5 h-3.5 animate-spin" />
                          : <Eye className="w-3.5 h-3.5" />}
                      </button>

                      {/* PDF/HTML download */}
                      <button
                        title="Download PDF / HTML report"
                        onClick={e => { e.stopPropagation(); downloadPDF(r); }}
                        disabled={!!busy}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-400 hover:text-red-300 transition-colors disabled:opacity-40">
                        {busy === 'pdf'
                          ? <Loader className="w-3.5 h-3.5 animate-spin" />
                          : <FileCode className="w-3.5 h-3.5" />}
                      </button>

                      {/* JSON download */}
                      <button
                        title="Download JSON"
                        onClick={e => { e.stopPropagation(); downloadJSON(r); }}
                        disabled={!!busy}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-purple-500/20 text-gray-400 hover:text-purple-300 transition-colors disabled:opacity-40">
                        {busy === 'json'
                          ? <Loader className="w-3.5 h-3.5 animate-spin" />
                          : <FileJson className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                  {r.summary && (
                    <p className="text-xs text-gray-400 mt-2 line-clamp-2">{r.summary}</p>
                  )}
                </motion.div>
              );
            })
          )}
        </div>

        {/* ── Report detail panel ── */}
        <div>
          {selectedReport ? (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
              className="glass-effect rounded-2xl border border-white/10 p-6 space-y-5 sticky top-20">

              <div className="flex justify-between items-start gap-3">
                <h3 className="font-semibold text-purple-300 text-sm font-mono truncate">
                  {selectedReport.report_id}
                </h3>
                {/* Download buttons in detail panel */}
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <button
                    onClick={() => previewReport(selectedReport)}
                    disabled={!!downloading[selectedReport.report_id]}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 text-xs transition-colors disabled:opacity-40">
                    {downloading[selectedReport.report_id] === 'preview'
                      ? <Loader className="w-3 h-3 animate-spin" />
                      : <Eye className="w-3 h-3" />}
                    <span>Preview</span>
                  </button>
                  <button
                    onClick={() => downloadPDF(selectedReport)}
                    disabled={!!downloading[selectedReport.report_id]}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs transition-colors disabled:opacity-40">
                    {downloading[selectedReport.report_id] === 'pdf'
                      ? <Loader className="w-3 h-3 animate-spin" />
                      : <Download className="w-3 h-3" />}
                    <span>PDF / HTML</span>
                  </button>
                  <button
                    onClick={() => downloadJSON(selectedReport)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 text-xs transition-colors">
                    <FileJson className="w-3 h-3" />
                    <span>JSON</span>
                  </button>
                </div>
              </div>

              {selectedReport.executive_summary && (
                <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Executive Summary</div>
                  <p className="text-sm text-gray-200 leading-relaxed">{selectedReport.executive_summary}</p>
                </div>
              )}

              {selectedReport.compliance_analysis && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Compliance Analysis</div>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      ['Score',        `${selectedReport.compliance_analysis.compliance_score ?? '—'}%`],
                      ['Coverage',     selectedReport.compliance_analysis.coverage_percentage ?? '—'],
                      ['Requirements', selectedReport.compliance_analysis.requirements_analyzed ?? '—'],
                      ['Gaps',         selectedReport.compliance_analysis.requirements_with_gaps ?? '—'],
                    ].map(([k, v]) => (
                      <div key={k} className="bg-white/5 rounded-lg p-3 text-center border border-white/5">
                        <div className="text-lg font-bold text-purple-300">{v}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{k}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedReport.challenge_audit && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Audit Findings</div>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      ['Critical', selectedReport.challenge_audit.critical_findings, 'text-red-400'],
                      ['High',     selectedReport.challenge_audit.high_findings,     'text-orange-400'],
                      ['Total',    selectedReport.challenge_audit.total_findings,    'text-yellow-400'],
                    ].map(([k, v, color]) => (
                      <div key={k} className="bg-white/5 rounded-lg p-2 text-center border border-white/5">
                        <div className={`text-lg font-bold ${color}`}>{v ?? '—'}</div>
                        <div className="text-xs text-gray-500">{k}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedReport.recommendations?.length > 0 && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Recommendations</div>
                  <div className="space-y-2">
                    {selectedReport.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start space-x-2 text-sm text-gray-300">
                        <div className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-2 flex-shrink-0" />
                        <span>{rec}</span>
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

      {/* ── HTML Preview Modal ── */}
      {previewOpen && previewHtml && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative w-full max-w-5xl h-[85vh] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 bg-gray-100 border-b border-gray-200">
              <span className="text-gray-700 font-medium text-sm">Report Preview</span>
              <div className="flex items-center space-x-2">
                <a href={previewHtml} download="compliance-report.html"
                  className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs hover:bg-indigo-700 transition-colors">
                  <Download className="w-3 h-3" /><span>Save HTML</span>
                </a>
                <button onClick={closePreview}
                  className="px-3 py-1.5 rounded-lg bg-gray-200 text-gray-700 text-xs hover:bg-gray-300 transition-colors">
                  Close
                </button>
              </div>
            </div>
            <iframe
              src={previewHtml}
              title="Compliance Report Preview"
              className="flex-1 w-full"
              sandbox="allow-same-origin"
            />
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Reports;
