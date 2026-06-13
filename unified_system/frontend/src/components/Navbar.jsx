import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield, Database, BarChart3, AlertTriangle, FileText,
  Settings, Sparkles, Network, Zap
} from 'lucide-react';

const Navbar = ({ apiStatus }) => {
  const location = useLocation();
  const [hoveredItem, setHoveredItem] = useState(null);

  const navItems = [
    { path: '/', icon: Shield, label: 'Dashboard', color: 'from-blue-400 to-cyan-400' },
    { path: '/copilot', icon: Sparkles, label: 'Copilot', color: 'from-violet-400 to-purple-400' },
    { path: '/evidence', icon: Database, label: 'Evidence', color: 'from-purple-400 to-pink-400' },
    { path: '/analysis', icon: BarChart3, label: 'Analysis', color: 'from-green-400 to-emerald-400' },
    { path: '/challenge-audit', icon: AlertTriangle, label: 'Challenge', color: 'from-orange-400 to-red-400' },
    { path: '/confidence', icon: Zap, label: 'Confidence', color: 'from-amber-400 to-orange-400' },
    { path: '/knowledge-graph', icon: Network, label: 'Graph', color: 'from-cyan-400 to-blue-400' },
    { path: '/reports', icon: FileText, label: 'Reports', color: 'from-indigo-400 to-purple-400' },
    { path: '/settings', icon: Settings, label: 'Settings', color: 'from-gray-400 to-slate-400' },
  ];

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 px-4 py-3 glass-effect border-b border-white/10"
    >
      <div className="max-w-screen-xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-3 group flex-shrink-0">
          <motion.div whileHover={{ rotate: 360, scale: 1.1 }} transition={{ duration: 0.6 }} className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg blur-md opacity-75 group-hover:opacity-100 transition-opacity" />
            <div className="relative bg-slate-900 p-2 rounded-lg">
              <Shield className="w-5 h-5 text-purple-400" />
            </div>
          </motion.div>
          <div className="hidden sm:block">
            <h1 className="text-base font-bold gradient-text leading-tight">Compliance Shield</h1>
            <p className="text-xs text-gray-500">Intelligence Platform</p>
          </div>
        </Link>

        {/* Nav Items */}
        <div className="flex items-center space-x-0.5 overflow-x-auto scrollbar-hide">
          {navItems.map((item, index) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link key={item.path} to={item.path}
                onMouseEnter={() => setHoveredItem(index)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`relative px-2.5 py-2 rounded-lg transition-all duration-300 ${
                    isActive ? 'bg-white/10 text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center space-x-1.5">
                    <Icon className="w-4 h-4" />
                    <span className="text-xs font-medium hidden lg:block whitespace-nowrap">{item.label}</span>
                  </div>
                  {isActive && (
                    <motion.div layoutId="activeTab"
                      className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r ${item.color}`}
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    />
                  )}
                </motion.div>
              </Link>
            );
          })}
        </div>

        {/* Status */}
        <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
          <div className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-full border text-xs font-medium ${
            apiStatus === 'connected'
              ? 'bg-green-500/10 border-green-500/20 text-green-400'
              : apiStatus === 'offline'
              ? 'bg-red-500/10 border-red-500/20 text-red-400'
              : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
          }`}>
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className={`w-1.5 h-1.5 rounded-full ${
                apiStatus === 'connected' ? 'bg-green-400' :
                apiStatus === 'offline' ? 'bg-red-400' : 'bg-yellow-400'
              }`}
            />
            <span>{apiStatus === 'connected' ? 'Live' : apiStatus === 'offline' ? 'Offline' : '...'}</span>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;

