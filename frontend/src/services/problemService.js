import { request } from './request';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export const getProblems = async () => {
  const response = await request.get('/api/problems');
  return response.data;
};

export const getProblem = async (id) => {
  const response = await request.get(`/api/problems/${id}`);
  return response.data;
};

export const createProblem = async (problem) => {
  const response = await request.post('/api/problems', problem);
  return response.data;
};

export const updateProblem = async (id, problem) => {
  const response = await request.put(`/api/problems/${id}`, problem);
  return response.data;
};

export const deleteProblem = async (id) => {
  const response = await request.delete(`/api/problems/${id}`);
  return response.data;
};

export const importProblems = async () => {
  const response = await request.post('/api/problems/import');
  return response.data;
};

export const exportProblems = async (problems) => {
  const response = await request.post('/api/problems/export', { problems });
  return response.data;
};

export const submitCode = async (candidateId, problemId, code, language) => {
  try {
    const response = await request.post('/api/submissions', {
      candidate_id: candidateId,
      problem_id: problemId,
      code,
      language,
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting code:', error);
    throw error;
  }
};

export const getSubmission = async (submissionId) => {
  try {
    const response = await request.get(`/api/submissions/${submissionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching submission:', error);
    throw error;
  }
};

export const getCandidateTabs = async (candidateId) => {
  try {
    const response = await request.get(`/api/candidates/${candidateId}/tabs`);
    return response.data;
  } catch (error) {
    console.error('Error fetching candidate tabs:', error);
    throw error;
  }
};

export const addCandidateTab = async (candidateId, problemId) => {
  try {
    const response = await request.post(`/api/candidates/${candidateId}/tabs`, {
      problem_id: problemId,
    });
    return response.data;
  } catch (error) {
    console.error('Error adding candidate tab:', error);
    throw error;
  }
};

export const removeCandidateTab = async (candidateId, problemId) => {
  try {
    const response = await request.delete(`/api/candidates/${candidateId}/tabs/${problemId}`);
    return response.data;
  } catch (error) {
    console.error('Error removing candidate tab:', error);
    throw error;
  }
};

export const pollSubmissionStatus = async (submissionId) => {
  try {
    const response = await request.get(`/api/submissions/${submissionId}/status`);
    return response.data;
  } catch (error) {
    console.error('Error polling submission status:', error);
    throw error;
  }
}; 
