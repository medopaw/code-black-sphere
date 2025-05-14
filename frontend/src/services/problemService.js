import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export const getProblems = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/problems`);
    return response.data;
  } catch (error) {
    console.error('Error fetching problems:', error);
    throw error;
  }
};

export const getProblem = async (problemId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/problems/${problemId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching problem:', error);
    throw error;
  }
};

export const submitCode = async (candidateId, problemId, code, language) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/submissions`, {
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
    const response = await axios.get(`${API_BASE_URL}/submissions/${submissionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching submission:', error);
    throw error;
  }
};

export const getCandidateTabs = async (candidateId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/candidates/${candidateId}/tabs`);
    return response.data;
  } catch (error) {
    console.error('Error fetching candidate tabs:', error);
    throw error;
  }
};

export const addCandidateTab = async (candidateId, problemId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/candidates/${candidateId}/tabs`, {
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
    const response = await axios.delete(
      `${API_BASE_URL}/candidates/${candidateId}/tabs/${problemId}`
    );
    return response.data;
  } catch (error) {
    console.error('Error removing candidate tab:', error);
    throw error;
  }
};

export const pollSubmissionStatus = async (submissionId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/submissions/${submissionId}/status`);
    return response.data;
  } catch (error) {
    console.error('Error polling submission status:', error);
    throw error;
  }
}; 
