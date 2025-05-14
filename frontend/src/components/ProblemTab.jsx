import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress, Alert, Snackbar } from '@mui/material';
import ProblemDescription from './ProblemDescription';
import CodeEditor from './CodeEditor';
import TestResults from './TestResults';
import LlmReview from './LlmReview';
import { getProblem, submitCode, getSubmission, pollSubmissionStatus } from '../services/problemService';

const POLLING_INTERVAL = 1000; // 1秒
const MAX_POLLING_TIME = 30000; // 30秒

const ProblemTab = ({ candidateId, problemId }) => {
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [code, setCode] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [llmReview, setLlmReview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionId, setSubmissionId] = useState(null);
  const [pollingError, setPollingError] = useState(null);

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

  useEffect(() => {
    let pollingTimer = null;
    let pollingStartTime = null;

    const pollStatus = async () => {
      if (!submissionId) return;

      try {
        const status = await pollSubmissionStatus(submissionId);
        
        if (status.status === 'completed') {
          // 获取完整的提交结果
          const submission = await getSubmission(submissionId);
          setTestResults(submission.test_results);
          setLlmReview(submission.llm_review);
          setSubmitting(false);
          setSubmissionId(null);
          return;
        }

        if (status.status === 'failed') {
          setPollingError('评测失败：' + (status.error || '未知错误'));
          setSubmitting(false);
          setSubmissionId(null);
          return;
        }

        // 检查是否超时
        if (Date.now() - pollingStartTime > MAX_POLLING_TIME) {
          setPollingError('评测超时，请稍后查看结果');
          setSubmitting(false);
          setSubmissionId(null);
          return;
        }

        // 继续轮询
        pollingTimer = setTimeout(pollStatus, POLLING_INTERVAL);
      } catch (err) {
        setPollingError('获取评测状态失败');
        setSubmitting(false);
        setSubmissionId(null);
        console.error('Error polling submission status:', err);
      }
    };

    if (submissionId) {
      pollingStartTime = Date.now();
      pollStatus();
    }

    return () => {
      if (pollingTimer) {
        clearTimeout(pollingTimer);
      }
    };
  }, [submissionId]);

  const handleCodeChange = (newCode) => {
    setCode(newCode);
  };

  const handleSubmit = async () => {
    if (!code.trim()) {
      setError('请先输入代码');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setPollingError(null);
      setTestResults(null);
      setLlmReview(null);

      const response = await submitCode(candidateId, problemId, code, problem.language);
      setSubmissionId(response.submission_id);
    } catch (err) {
      setError('提交代码失败');
      setSubmitting(false);
      console.error('Error submitting code:', err);
    }
  };

  const handleCloseError = () => {
    setError(null);
  };

  const handleClosePollingError = () => {
    setPollingError(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
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
          submitting={submitting}
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

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!pollingError}
        autoHideDuration={6000}
        onClose={handleClosePollingError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleClosePollingError} severity="warning" sx={{ width: '100%' }}>
          {pollingError}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProblemTab; 
