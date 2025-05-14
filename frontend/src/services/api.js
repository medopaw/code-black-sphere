import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 候选人相关 API
export const candidateApi = {
  create: (data) => api.post('/candidates', data),
  getAll: () => api.get('/candidates'),
  getById: (id) => api.get(`/candidates/${id}`),
  update: (id, data) => api.put(`/candidates/${id}`, data),
  delete: (id) => api.delete(`/candidates/${id}`),
};

// 题目相关 API
export const problemApi = {
  create: (data) => api.post('/problems', data),
  getAll: () => api.get('/problems'),
  getById: (id) => api.get(`/problems/${id}`),
  update: (id, data) => api.put(`/problems/${id}`, data),
  delete: (id) => api.delete(`/problems/${id}`),
  import: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/problems/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  export: () => api.get('/problems/export', { responseType: 'blob' }),
};

// 测试用例相关 API
export const testCaseApi = {
  create: (problemId, data) => api.post(`/problems/${problemId}/testcases`, data),
  getAll: (problemId) => api.get(`/problems/${problemId}/testcases`),
  getById: (id) => api.get(`/testcases/${id}`),
  update: (id, data) => api.put(`/testcases/${id}`, data),
  delete: (id) => api.delete(`/testcases/${id}`),
};

// 提交相关 API
export const submissionApi = {
  create: (data) => api.post('/submissions', data),
  getAll: () => api.get('/submissions'),
  getById: (id) => api.get(`/submissions/${id}`),
  getByCandidateAndProblem: (candidateId, problemId) => 
    api.get(`/submissions/candidate/${candidateId}/problem/${problemId}`),
};

// Tab 相关 API
export const tabApi = {
  create: (candidateId, data) => api.post(`/candidates/${candidateId}/tabs`, data),
  getAll: (candidateId) => api.get(`/candidates/${candidateId}/tabs`),
  delete: (candidateId, problemId) => 
    api.delete(`/candidates/${candidateId}/tabs/${problemId}`),
  updateOrder: (candidateId, data) => 
    api.put(`/candidates/${candidateId}/tabs`, data),
};

// 设置相关 API
export const settingApi = {
  getAll: () => api.get('/settings'),
  getByKey: (key) => api.get(`/settings/${key}`),
  update: (key, value) => api.put(`/settings/${key}`, { value }),
};

export default api; 
