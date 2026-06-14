import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Send, Loader2, User, Sparkles, History, Shield } from 'lucide-react';
import { copilotAPI } from '../api/client.jsx';

const SUGGESTIONS = [
  'Show GDPR compliance status',
  'Which requirements are missing evidence?',
  'Show NIST gaps',
  'What is the current system status?',
  'Show SOX compliance',
  'What evidence is stale?',
];

const MessageBubble = ({ msg }) => {
  const isUser = msg.role === 'user';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, x: isUser ? 20 : -20 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      {!isUser && (
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mr-3 flex-shrink-0 mt-1">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      <div className={`max-w-[78%] ${isUser ? 'order-1' : ''}`}>
        <div className={`rounded-2xl px-5 py-3 ${
          isUser
            ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
            : 'bg-white/5 border border-white/10 text-gray-100'
        }`}>
          {msg.loading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
              <span className="text-gray-400 text-sm">Thinking...</span>
            </div>
          ) : (
            <div className="whitespace-pre-line text-sm leading-relaxed">
              {msg.content}
            </div>
          )}
        </div>
        {!isUser && msg.confidence && !msg.loading && (
          <div className="mt-1 ml-2 flex items-center space-x-2">
            <span className="text-xs text-gray-500">Confidence:</span>
            <span className={`text-xs font-medium ${
              msg.confidence >= 0.8 ? 'text-green-400' :
              msg.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
            }`}>{(msg.confidence * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center ml-3 flex-shrink-0 mt-1">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </motion.div>
  );
};

const ComplianceCopilot = () => {
  const [messages, setMessages] = useState([
    {
      id: 0, role: 'assistant',
      content: "Hello! I'm the Compliance Copilot. I can help you query your compliance posture, find gaps, and understand requirements.\n\nTry asking me:\n• 'Show GDPR compliance status'\n• 'Which requirements are missing evidence?'\n• 'Show NIST gaps'",
      confidence: 1.0,
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const q = text || input.trim();
    if (!q) return;
    setInput('');

    const userMsg = { id: Date.now(), role: 'user', content: q };
    const loadingMsg = { id: Date.now() + 1, role: 'assistant', content: '', loading: true };
    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setLoading(true);

    try {
      const res = await copilotAPI.query(q);
      const data = res.data;
      setMessages(prev => prev.map(m =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, content: data.answer || data.answer_summary || 'No response', confidence: data.confidence }
          : m
      ));
    } catch (e) {
      setMessages(prev => prev.map(m =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, content: `Error: ${e}`, confidence: 0 }
          : m
      ));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-6 flex flex-col max-w-5xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-violet-600 via-purple-600 to-pink-600 mb-6"
      >
        <div className="relative z-10 flex items-center space-x-4">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            <Sparkles className="w-12 h-12 text-yellow-300" />
          </motion.div>
          <div>
            <h1 className="text-4xl font-bold">Compliance Copilot</h1>
            <p className="text-purple-100 mt-1">AI-powered natural language interface for compliance queries</p>
          </div>
          <div className="ml-auto flex items-center space-x-2 px-3 py-1.5 rounded-full bg-white/20">
            <div className="w-2 h-2 rounded-full bg-green-300 animate-pulse" />
            <span className="text-sm font-medium">Online</span>
          </div>
        </div>
      </motion.div>

      <div className="flex gap-6 flex-1">
        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 glass-effect rounded-2xl border border-white/10 p-4 overflow-y-auto min-h-96 max-h-[55vh]">
            {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="mt-4 flex space-x-3">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
              placeholder="Ask a compliance question..."
              disabled={loading}
              className="flex-1 glass-effect rounded-xl px-5 py-3 border border-white/10 focus:outline-none focus:border-purple-500 transition-colors text-sm disabled:opacity-50"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => send()}
              disabled={loading || !input.trim()}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 font-medium transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              <span className="hidden sm:inline">Send</span>
            </motion.button>
          </div>
        </div>

        {/* Sidebar: suggestions */}
        <div className="w-64 space-y-4">
          <div className="glass-effect rounded-2xl border border-white/10 p-4">
            <h3 className="font-semibold text-sm text-gray-300 mb-3 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span>Suggested Queries</span>
            </h3>
            <div className="space-y-2">
              {SUGGESTIONS.map((s, i) => (
                <motion.button
                  key={i}
                  whileHover={{ x: 4 }}
                  onClick={() => send(s)}
                  disabled={loading}
                  className="w-full text-left text-xs text-gray-300 hover:text-white px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5 disabled:opacity-50"
                >
                  {s}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="glass-effect rounded-2xl border border-white/10 p-4">
            <h3 className="font-semibold text-sm text-gray-300 mb-3 flex items-center space-x-2">
              <Shield className="w-4 h-4 text-blue-400" />
              <span>Pipeline</span>
            </h3>
            <div className="space-y-2 text-xs text-gray-400">
              {[
                'Compliance Copilot', 'LLM Requirement Extractor',
                'Semantic Mapper', 'Knowledge Graph',
                'Challenge Auditor', 'Confidence Engine',
                'Narrative Generator', 'Report',
              ].map((step, i) => (
                <div key={i} className="flex items-center space-x-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${i === 0 ? 'bg-purple-400 animate-pulse' : 'bg-gray-600'}`} />
                  <span className={i === 0 ? 'text-purple-300 font-medium' : ''}>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceCopilot;

