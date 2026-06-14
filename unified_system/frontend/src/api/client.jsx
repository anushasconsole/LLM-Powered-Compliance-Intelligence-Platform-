import axios from 'axios';

// In dev: Vite proxies /api → http://localhost:5000
// In prod: set VITE_API_URL env var
const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Unwrap { status, data } envelope automatically
api.interceptors.response.use(
  (res) => {
    if (res.data && res.data.data !== undefined) {
      return { ...res, data: res.data.data };
    }
    return res;
  },
  (err) => Promise.reject(err?.response?.data?.message || err.message || 'Request failed')
);

export const healthAPI = {
  check:  () => api.get('/api/health'),
  status: () => api.get('/api/status'),
};

export const initAPI = {
  initialize: (body = {}) => api.post('/api/initialize', body),
  initText:   (policy_text, evidence_csv) =>
    api.post('/api/initialize/text', { policy_text, evidence_csv }),
};

export const dashboardAPI = {
  get:        () => api.get('/api/dashboard'),
  frameworks: () => api.get('/api/frameworks'),
};

export const analysisAPI = {
  run:        (framework = 'ALL') => api.get(`/api/analysis/${framework}`),
  confidence: (framework = 'ALL') => api.get(`/api/confidence/${framework}`),
};

export const challengeAPI = {
  run:      (framework = 'ALL') => api.post(`/api/challenge-audit/${framework}`),
  findings: (framework = null)  =>
    api.get('/api/challenge-findings', { params: framework ? { framework } : {} }),
};

export const evidenceAPI = {
  getAll:  (params = {}) => api.get('/api/evidence', { params }),
  getById: (id)          => api.get(`/api/evidence/${id}`),
  upload:  (data)        => api.post('/api/evidence', data),
};

export const requirementsAPI = {
  getAll:  (params = {}) => api.get('/api/requirements', { params }),
  getById: (id)          => api.get(`/api/requirements/${id}`),
};

export const reportsAPI = {
  getAll:      ()               => api.get('/api/reports'),
  getById:     (id)             => api.get(`/api/reports/${id}`),
  generate:    (framework = 'ALL') => api.post('/api/reports/generate', { framework }),
  downloadPdf: (id)             => api.get(`/api/reports/${id}/pdf`, { responseType: 'blob' }),
};

export const copilotAPI = {
  query:   (q) => api.post('/api/copilot', { query: q }),
  history: ()  => api.get('/api/copilot/history'),
};

export const knowledgeGraphAPI = {
  get: () => api.get('/api/knowledge-graph'),
};

export const mappingsAPI = {
  getAll:  () => api.get('/api/mappings'),
  rebuild: () => api.post('/api/mappings/rebuild'),
};

export const anomalyAPI = {
  detect:   (body = {}) => api.post('/api/anomaly/detect', body),
  evaluate: (body = {}) => api.post('/api/anomaly/evaluate', body),
  summary:  (threshold) => api.get('/api/anomaly/summary', { params: threshold ? { threshold } : {} }),
};

export const integrationsAPI = {
  list:          ()           => api.get('/api/integrations'),
  collectAll:    (sources)    => api.post('/api/integrations/collect', sources ? { sources } : {}),
  collectOne:    (sourceId)   => api.post(`/api/integrations/collect/${sourceId}`),
};

export default api;
