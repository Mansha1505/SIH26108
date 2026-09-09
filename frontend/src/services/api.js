import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';


const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const recommendStandards = async (query, topK = 5) => {
  const response = await apiClient.post('/recommend', {
    query: query.trim(),
    top_k: parseInt(topK, 10),
  });
  return response.data;
};

export const recommendFromRequirements = async (requirements, topK = 5) => {
  const response = await apiClient.post('/recommend/from-requirements', {
    requirements: requirements,
    top_k: parseInt(topK, 10),
  });
  return response.data;
};

export const extractDocumentText = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/documents/extract', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 30000,
  });
  return response.data;
};

export const extractRequirements = async (text, filename = null) => {
  const response = await apiClient.post('/documents/extract-requirements', {
    text: text,
    filename: filename,
  });
  return response.data;
};

export const getStandardsAmendments = async () => {
  const response = await apiClient.get('/standards/amendments');
  return response.data;
};

export const getStandardsNetwork = async () => {
  const response = await apiClient.get('/standards/network');
  return response.data;
};

export const getStandardSubgraph = async (standardId, depth = 1) => {
  const response = await apiClient.get(`/standards/network/${encodeURIComponent(standardId)}`, {
    params: { depth }
  });
  return response.data;
};

export const getCertificationRules = async () => {
  const response = await apiClient.get('/certification/rules');
  return response.data;
};

export const assessCertification = async (standardIds = [], productCategory = null) => {
  const response = await apiClient.post('/certification/assess', {
    standard_ids: standardIds,
    product_category: productCategory,
  });
  return response.data;
};

export const explainRecommendations = async (query, topK = 5) => {
  const response = await apiClient.post('/recommend/explain', {
    query: query.trim(),
    top_k: parseInt(topK, 10),
  });
  return response.data;
};

export const analyzeGaps = async (query = '', topK = 5, requirements = null) => {
  const response = await apiClient.post('/recommend/gap-analysis', {
    query: query ? query.trim() : '',
    requirements: requirements,
    top_k: parseInt(topK, 10),
  });
  return response.data;
};

export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export const generateReport = async (query = '', topK = 5, requirements = null, filename = null) => {
  const response = await apiClient.post('/reports/generate', {
    query: query ? query.trim() : null,
    requirements: requirements,
    top_k: parseInt(topK, 10),
    uploaded_document_name: filename,
  });
  return response.data;
};

export const downloadReportJson = async (query = '', topK = 5, requirements = null, filename = null) => {
  const response = await apiClient.post('/reports/export/json', {
    query: query ? query.trim() : null,
    requirements: requirements,
    top_k: parseInt(topK, 10),
    uploaded_document_name: filename,
  });

  const jsonStr = JSON.stringify(response.data, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const repId = response.data?.metadata?.report_id || `REPORT-${Date.now()}`;
  link.setAttribute('download', `procurement_standards_report_${repId}.json`);
  document.body.appendChild(link);
  link.click();
  if (link.parentNode) {
    link.parentNode.removeChild(link);
  }
  window.URL.revokeObjectURL(url);
  return response.data;
};

export const downloadReportPdf = async (query = '', topK = 5, requirements = null, filename = null) => {
  const response = await apiClient.post(
    '/reports/export/pdf',
    {
      query: query ? query.trim() : null,
      requirements: requirements,
      top_k: parseInt(topK, 10),
      uploaded_document_name: filename,
    },
    {
      responseType: 'blob',
    }
  );

  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;

  let downloadName = `procurement_standards_report_${Date.now()}.pdf`;
  const disposition = response.headers['content-disposition'];
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      downloadName = match[1];
    }
  }

  link.setAttribute('download', downloadName);
  document.body.appendChild(link);
  link.click();
  if (link.parentNode) {
    link.parentNode.removeChild(link);
  }
  window.URL.revokeObjectURL(url);
  return true;
};




