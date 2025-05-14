import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import ProblemDescription from './ProblemDescription';
import CodeEditor from './CodeEditor';
import TestResults from './TestResults';
import LlmReview from './LlmReview';
import { getProblem } from '../services/problemService';

const ProblemTab = ({ candidateId, problemId }) => {
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [code, setCode] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [llmReview, setLlmReview] = useState(null);

  useEffect(() => {
    const fetchProblem = async () => {
      try {
        setLoading(true);
        const data = await getProblem(problemId);
        setProblem(data);
        setError(null);
      } catch (err) {
        setError('加载题目失败');
        console.error('Error fetching problem:', err);
      } finally {
        setLoading(false);
      }
    };

    if (problemId) {
      fetchProblem();
    }
  }, [problemId]);

  const handleCodeChange = (newCode) => {
    setCode(newCode);
  };

  const handleSubmit = async () => {
    // TODO: 实现代码提交和评测逻辑
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!problem) {
    return null;
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, gap: 2 }}>
      <Paper sx={{ p: 2 }}>
        <ProblemDescription description={problem.description} />
      </Paper>

      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <CodeEditor
          code={code}
          onChange={handleCodeChange}
          onSubmit={handleSubmit}
          language={problem.language}
        />
      </Paper>

      {testResults && (
        <Paper sx={{ p: 2 }}>
          <TestResults results={testResults} />
        </Paper>
      )}

      {llmReview && (
        <Paper sx={{ p: 2 }}>
          <LlmReview review={llmReview} />
        </Paper>
      )}
    </Box>
  );
};

export default ProblemTab; 
