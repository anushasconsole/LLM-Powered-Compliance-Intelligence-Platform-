import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, Database, CheckCircle, AlertTriangle, TrendingUp, Activity, Zap, Award, RefreshCw, Sparkles } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { dashboardAPI, initAPI } from '../api/client.jsx';

const FRAMEWORK_COLORS = {
  'GDPR': '#10b981', 'SOX': '#3b82f6', 'NIST': '#8b5cf6',
  'PCI-DSS': '#ec4899', 'ISO27001': '#f59e0b', 'HIPAA': '#06b6d4', 'CIS': '#84cc16',
};

const Dashboard = () => {
  const [selectedFramework, setSelectedFramework] = useState('ALL');
  const [animatedScore, setAnimatedScore] = useState(0);
  const [dashData, setDashData] = useState(null);
  const [frameworks, setFrameworks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(false);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [dashRes, fwRes] = await Promise.all([dashboardAPI.get(), dashboardAPI.frameworks()]);
      setDashData(dashRes.data);
      const fwData = (fwRes.data || []).map(fw => ({
        ...fw,
        color: FRAMEWORK_COLORS[fw.name] || '#64748b',
        status: fw.score >= 85 ? 'excellent' : fw.score >= 70 ? 'good' : 'acceptable',
      }));
      setFrameworks(fwData);
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  };

  const initSystem = async () => {
    setInitializing(true);
    try {
      await initAPI.initialize({});
      await loadDashboard();
    } catch (e) {
      console.error(e);
    } finally {
      setInitializing(false);
    }
  };

  useEffect(() => { loadDashboard(); }, []);

  useEffect(() => {
    let current = 0;
    const target = dashData?.complianceScore || 0;
    if (target === 0) return;
    const increment = target / 50;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) { setAnimatedScore(target); clearInterval(timer); }
      else setAnimatedScore(current);
    }, 20);
    return () => clearInterval(timer);
  }, [dashData]);

  const trendData = [
    { month: 'Jan', score: 65 }, { month: 'Feb', score: 68 },
    { month: 'Mar', score: 72 }, { month: 'Apr', score: 75 },
    { month: 'May', score: 77 }, { month: 'Jun', score: animatedScore },
  ];

  const evidenceDistribution = [
    { name: 'Config', value: 150, color: '#8b5cf6' },
    { name: 'Audit Logs', value: 120, color: '#ec4899' },
    { name: 'Certificates', value: 80, color: '#10b981' },
    { name: 'Tests', value: 90, color: '#f59e0b' },
    { name: 'Reports', value: 60, color: '#3b82f6' },
  ];

  const radarData = frameworks.map(f => ({
    framework: f.name, score: f.score, fullMark: 100
  }));

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="min-h-screen p-6 space-y-6"
    >
      {/* Hero Section */}
      <motion.div variants={item} className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 animate-gradient">
        <div className="absolute inset-0 opacity-20">
          <div className="cyber-grid h-full"></div>
        </div>
        <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
          <div>
            <motion.h1 initial={{ x: -50, opacity: 0 }} animate={{ x: 0, opacity: 1 }}
              className="text-4xl font-bold mb-2 flex items-center space-x-3">
              <motion.div animate={{ rotate: [0, 360] }} transition={{ duration: 20, repeat: Infinity, ease: "linear" }}>
                <Shield className="w-10 h-10" />
              </motion.div>
              <span>Compliance Command Center</span>
            </motion.h1>
            <p className="text-purple-100">Real-time compliance monitoring · AI-powered intelligence</p>
          </div>
          <div className="flex space-x-3">
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={loadDashboard} disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-sm font-medium disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={initSystem} disabled={initializing}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-sm font-medium disabled:opacity-50">
              <Sparkles className={`w-4 h-4 ${initializing ? 'animate-spin' : ''}`} />
              <span>{initializing ? 'Initializing...' : 'Initialize System'}</span>
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div variants={item} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { icon: Database, label: 'Total Evidence', value: dashData?.totalEvidence ?? '—', color: 'from-blue-500 to-cyan-500', bgColor: 'bg-blue-500/10' },
          { icon: CheckCircle, label: 'Requirements', value: dashData?.totalRequirements ?? '—', color: 'from-green-500 to-emerald-500', bgColor: 'bg-green-500/10' },
          { icon: TrendingUp, label: 'Compliance Score', value: `${animatedScore.toFixed(1)}%`, color: 'from-purple-500 to-pink-500', bgColor: 'bg-purple-500/10' },
          { icon: AlertTriangle, label: 'Critical Findings', value: dashData?.criticalFindings ?? '—', color: 'from-orange-500 to-red-500', bgColor: 'bg-orange-500/10' },
        ].map((metric, index) => {
          const Icon = metric.icon;
          return (
            <motion.div
              key={index}
              whileHover={{ scale: 1.05, y: -10 }}
              className="relative group"
            >
              <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl blur-xl" style={{ background: `linear-gradient(to right, ${metric.color})` }}></div>
              <div className="relative glass-effect rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300">
                <div className={`w-14 h-14 rounded-xl ${metric.bgColor} flex items-center justify-center mb-4`}>
                  <Icon className="w-7 h-7" style={{ color: metric.color.split(' ')[1] }} />
                </div>
                <p className="text-gray-400 text-sm mb-1">{metric.label}</p>
                <motion.p
                  className="text-3xl font-bold"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.3 + index * 0.1, type: "spring" }}
                >
                  {metric.value}
                </motion.p>
                <div className="mt-3 flex items-center text-green-400 text-sm">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  <span>+12% this month</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Framework Cards */}
      <motion.div variants={item} className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold flex items-center space-x-2">
            <Activity className="w-6 h-6 text-purple-400" />
            <span>Framework Compliance Scores</span>
          </h2>
          <select
            value={selectedFramework}
            onChange={(e) => setSelectedFramework(e.target.value)}
            className="glass-effect px-4 py-2 rounded-lg border border-white/10 focus:outline-none focus:border-purple-500 transition-colors"
          >
            <option value="ALL">All Frameworks</option>
            {frameworks.map(f => <option key={f.name} value={f.name}>{f.name}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {frameworks.map((framework, index) => (
            <motion.div
              key={framework.name}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 * index }}
              whileHover={{ scale: 1.05, rotate: 1 }}
              className="glass-effect rounded-xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 cursor-pointer group"
              style={{
                boxShadow: `0 10px 40px ${framework.color}15`
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{framework.name}</h3>
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                  className="w-10 h-10 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: `${framework.color}20` }}
                >
                  <Award className="w-5 h-5" style={{ color: framework.color }} />
                </motion.div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Compliance Score</span>
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="font-bold text-xl"
                    style={{ color: framework.color }}
                  >
                    {framework.score}%
                  </motion.span>
                </div>

                <div className="relative h-3 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${framework.score}%` }}
                    transition={{ duration: 1, delay: 0.2 * index }}
                    className="absolute h-full rounded-full"
                    style={{
                      background: `linear-gradient(to right, ${framework.color}, ${framework.color}dd)`
                    }}
                  />
                  <motion.div
                    animate={{ x: [0, 200, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="absolute h-full w-20 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    framework.status === 'excellent' ? 'bg-green-500/20 text-green-400' :
                    framework.status === 'good' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {framework.status.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-400">45/50 Requirements</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Charts Section */}
      <motion.div variants={item} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Trend */}
        <div className="glass-effect rounded-2xl p-6 border border-white/10">
          <h3 className="text-xl font-bold mb-6 flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <span>Compliance Trend</span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="month" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
              <Line type="monotone" dataKey="score" stroke="#8b5cf6" strokeWidth={3} dot={{ fill: '#8b5cf6', r: 6 }} activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Evidence Distribution */}
        <div className="glass-effect rounded-2xl p-6 border border-white/10">
          <h3 className="text-xl font-bold mb-6 flex items-center space-x-2">
            <Database className="w-5 h-5 text-blue-400" />
            <span>Evidence Distribution</span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={evidenceDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {evidenceDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Radar Chart */}
        <div className="glass-effect rounded-2xl p-6 border border-white/10 lg:col-span-2">
          <h3 className="text-xl font-bold mb-6 flex items-center space-x-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <span>Framework Comparison</span>
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="framework" stroke="#64748b" />
              <PolarRadiusAxis stroke="#64748b" />
              <Radar name="Compliance Score" dataKey="score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Recent Activity */}
      <motion.div variants={item} className="glass-effect rounded-2xl p-6 border border-white/10">
        <h3 className="text-xl font-bold mb-6">Recent Activity</h3>
        <div className="space-y-4">
          {[
            { action: 'Evidence uploaded', detail: 'AWS KMS Configuration', time: '2 minutes ago', type: 'success' },
            { action: 'Challenge audit completed', detail: 'GDPR Framework', time: '15 minutes ago', type: 'warning' },
            { action: 'Report generated', detail: 'Q2 2026 Compliance Report', time: '1 hour ago', type: 'info' },
            { action: 'Critical finding resolved', detail: 'Backup encryption verified', time: '3 hours ago', type: 'success' },
          ].map((activity, index) => (
            <motion.div
              key={index}
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1 * index }}
              whileHover={{ x: 10 }}
              className="flex items-center space-x-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer group"
            >
              <div className={`w-2 h-2 rounded-full ${
                activity.type === 'success' ? 'bg-green-400' :
                activity.type === 'warning' ? 'bg-yellow-400' :
                'bg-blue-400'
              } animate-pulse`} />
              <div className="flex-1">
                <p className="font-medium group-hover:text-purple-400 transition-colors">{activity.action}</p>
                <p className="text-sm text-gray-400">{activity.detail}</p>
              </div>
              <span className="text-xs text-gray-500">{activity.time}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Dashboard;

