import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, message, Space, Tabs } from 'antd';
import { SaveOutlined, PreviewOutlined } from '@ant-design/icons';
import BasicInfoEditor from './BasicInfoEditor';
import MarkdownEditor from './MarkdownEditor';
import TestCaseManager from './TestCaseManager';
import PromptEditor from './PromptEditor';
import PreviewPanel from './PreviewPanel';
import { getProblem, createProblem, updateProblem } from '../../services/problemService';
import './index.css';

const ProblemEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [problem, setProblem] = useState({
    title: '',
    description: '',
    llm_prompt: '',
    test_cases: []
  });
  const [activeTab, setActiveTab] = useState('basic');

  useEffect(() => {
    if (id) {
      loadProblem();
    }
  }, [id]);

  const loadProblem = async () => {
    try {
      setLoading(true);
      const data = await getProblem(id);
      setProblem(data);
    } catch (error) {
      message.error('加载题目失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      if (id) {
        await updateProblem(id, problem);
        message.success('更新题目成功');
      } else {
        const newProblem = await createProblem(problem);
        message.success('创建题目成功');
        navigate(`/problems/edit/${newProblem.id}`);
      }
    } catch (error) {
      message.error('保存题目失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProblemChange = (field, value) => {
    setProblem(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const items = [
    {
      key: 'basic',
      label: '基本信息',
      children: <BasicInfoEditor problem={problem} onChange={handleProblemChange} />
    },
    {
      key: 'description',
      label: '题目描述',
      children: <MarkdownEditor value={problem.description} onChange={(value) => handleProblemChange('description', value)} />
    },
    {
      key: 'testcases',
      label: '测试用例',
      children: <TestCaseManager testCases={problem.test_cases} onChange={(value) => handleProblemChange('test_cases', value)} />
    },
    {
      key: 'prompt',
      label: 'LLM Prompt',
      children: <PromptEditor value={problem.llm_prompt} onChange={(value) => handleProblemChange('llm_prompt', value)} />
    }
  ];

  return (
    <div className="problem-editor">
      <Card
        title={id ? '编辑题目' : '新建题目'}
        extra={
          <Space>
            <Button
              icon={<PreviewOutlined />}
              onClick={() => setActiveTab('preview')}
            >
              预览
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              loading={loading}
            >
              保存
            </Button>
          </Space>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={activeTab === 'preview' ? [
            {
              key: 'preview',
              label: '预览',
              children: <PreviewPanel problem={problem} />
            }
          ] : items}
        />
      </Card>
    </div>
  );
};

export default ProblemEditor; 
