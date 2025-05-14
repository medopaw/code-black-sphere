import React from 'react';
import { Card, Tag, Space } from 'antd';
import MDEditor from '@uiw/react-md-editor';
import './PreviewPanel.css';

const DIFFICULTY_COLORS = {
  easy: 'success',
  medium: 'warning',
  hard: 'error'
};

const DIFFICULTY_LABELS = {
  easy: '简单',
  medium: '中等',
  hard: '困难'
};

const CATEGORY_LABELS = {
  'algorithm': '算法',
  'data-structure': '数据结构',
  'system-design': '系统设计',
  'database': '数据库',
  'network': '网络'
};

const PreviewPanel = ({ problem }) => {
  return (
    <div className="preview-panel">
      <Card>
        <div className="problem-header">
          <h1>{problem.title}</h1>
          <Space>
            {problem.difficulty && (
              <Tag color={DIFFICULTY_COLORS[problem.difficulty]}>
                {DIFFICULTY_LABELS[problem.difficulty]}
              </Tag>
            )}
            {problem.categories?.map(category => (
              <Tag key={category}>{CATEGORY_LABELS[category]}</Tag>
            ))}
          </Space>
        </div>

        <div className="problem-description">
          <MDEditor.Markdown source={problem.description} />
        </div>

        <div className="test-cases">
          <h2>测试用例</h2>
          {problem.test_cases?.map((testCase, index) => (
            <Card key={testCase.id} className="test-case-card">
              <h3>测试用例 {index + 1}</h3>
              <div className="test-case-content">
                <div>
                  <h4>输入参数：</h4>
                  <pre>{JSON.stringify(JSON.parse(testCase.input_params), null, 2)}</pre>
                </div>
                <div>
                  <h4>预期输出：</h4>
                  <pre>{JSON.stringify(JSON.parse(testCase.expected_output), null, 2)}</pre>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="llm-prompt">
          <h2>LLM Prompt 模板</h2>
          <pre className="prompt-content">{problem.llm_prompt}</pre>
        </div>
      </Card>
    </div>
  );
};

export default PreviewPanel; 
