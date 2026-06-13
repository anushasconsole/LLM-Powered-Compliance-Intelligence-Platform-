import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Components
import Navbar from './components/Navbar.jsx';
import ParticlesBackground from './components/ParticlesBackground.jsx';

// Pages
import Dashboard from './pages/Dashboard.jsx';
import Evidence from './pages/Evidence.jsx';
import Analysis from './pages/Analysis.jsx';
import ChallengeAudit from './pages/ChallengeAudit.jsx';
import Reports from './pages/Reports.jsx';
import Settings from './pages/Settings.jsx';
import ComplianceCopilot from './pages/ComplianceCopilot.jsx';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage.jsx';
import ConfidencePage from './pages/ConfidencePage.jsx';

import { healthAPI } from './api/client.jsx';

function App() {
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState('connecting');

  useEffect(() => {
    const init = async () => {
      try {
        await healthAPI.check();
        setApiStatus('connected');
      } catch {
        setApiStatus('offline');
      } finally {
        setTimeout(() => setLoading(false), 1800);
      }
    };
    init();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div
            className="w-32 h-32 mx-auto mb-8 relative"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-75 blur-xl" />
            <div className="absolute inset-2 rounded-full bg-slate-900 flex items-center justify-center">
              <svg className="w-16 h-16 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </motion.div>
          <motion.h2
            className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            Compliance Intelligence Platform
          </motion.h2>
          <motion.p
            className="text-gray-400 mt-3"
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            Initializing AI compliance engine...
          </motion.p>
          <motion.div
            className="mt-4 flex items-center justify-center space-x-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <div className={`w-2 h-2 rounded-full ${apiStatus === 'connected' ? 'bg-green-400' : apiStatus === 'offline' ? 'bg-red-400' : 'bg-yellow-400'} animate-pulse`} />
            <span className="text-xs text-gray-500">
              API {apiStatus === 'connected' ? 'connected' : apiStatus === 'offline' ? 'offline — check backend' : 'connecting...'}
            </span>
          </motion.div>
        </motion.div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-slate-950 text-white relative overflow-hidden">
        <ParticlesBackground />
        {/* Ambient gradients */}
        <div className="fixed inset-0 opacity-20 pointer-events-none">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl animate-float" />
          <div className="absolute top-0 right-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl animate-float animation-delay-2000" />
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl animate-float animation-delay-4000" />
        </div>

        <div className="relative z-10">
          <Navbar apiStatus={apiStatus} />
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/copilot" element={<ComplianceCopilot />} />
              <Route path="/evidence" element={<Evidence />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/challenge-audit" element={<ChallengeAudit />} />
              <Route path="/confidence" element={<ConfidencePage />} />
              <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </AnimatePresence>
        </div>
      </div>
    </Router>
  );
}

export default App;

