import React, { useState } from 'react';
import { Card, Input, Button, Space, message } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import { testPrompt } from '../../services/llmService';
import './PromptEditor.css';

const { TextArea } = Input;

const PromptEditor = ({ value, onChange }) => {
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTest = async () => {
    try {
      setLoading(true);
      const response = await testPrompt(value);
      setPreview(response);
      message.success('Prompt 测试成功');
    } catch (error) {
      console.error('Prompt test failed:', error);
      message.error('Prompt 测试失败：' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    onChange(newValue);
    
    // 简单的变量替换预览
    const previewText = newValue
      .replace(/\{\{code\}\}/g, '// 示例代码\nfunction example() {\n  return "Hello World";\n}')
      .replace(/\{\{test_results\}\}/g, JSON.stringify({
        passed: true,
        output: 'Hello World',
        error: null
      }, null, 2));
    
    setPreview(previewText);
  };

  return (
    <div className="prompt-editor">
      <Card title="LLM Prompt 模板">
        <TextArea
          value={value}
          onChange={handleChange}
          placeholder="输入 Prompt 模板，使用 {{variable}} 语法引用变量"
          rows={10}
        />
        
        <div className="editor-toolbar">
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleTest}
              loading={loading}
            >
              测试 Prompt
            </Button>
          </Space>
        </div>
      </Card>

      <Card title="变量替换预览" className="preview-card">
        <pre className="preview-content">{preview}</pre>
      </Card>
    </div>
  );
};

export default PromptEditor; 
