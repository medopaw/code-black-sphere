import React, { useState, useEffect } from 'react';
import { Card, Select, Button, Table, Space, Modal, Input, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ImportOutlined, ExportOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getProblems, deleteProblem, importProblems, exportProblems } from '../../services/problemService';
import { getSettings, updateSetting } from '../../services/settingService';
import './index.css';

const Settings = () => {
  const navigate = useNavigate();
  const [problems, setProblems] = useState([]);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [problemsData, settingsData] = await Promise.all([
        getProblems(),
        getSettings()
      ]);
      setProblems(problemsData);
      setSettings(settingsData);
      setApiKey(settingsData.deepseek_api_key || '');
    } catch (error) {
      console.error('Load data failed:', error);
      message.error('加载数据失败：' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const handleDefaultProblemChange = async (value) => {
    try {
      await updateSetting('default_problem_id', value);
      setSettings(prev => ({ ...prev, default_problem_id: value }));
      message.success('默认题目设置已更新');
    } catch (error) {
      console.error('Update default problem failed:', error);
      message.error('更新默认题目失败：' + (error.message || '未知错误'));
    }
  };

  const handleApiKeyChange = async () => {
    try {
      await updateSetting('deepseek_api_key', apiKey);
      setSettings(prev => ({ ...prev, deepseek_api_key: apiKey }));
      message.success('API Key 已更新');
    } catch (error) {
      console.error('Update API key failed:', error);
      message.error('更新 API Key 失败：' + (error.message || '未知错误'));
    }
  };

  const handleDeleteProblem = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个题目吗？此操作不可恢复。',
      onOk: async () => {
        try {
          await deleteProblem(id);
          setProblems(prev => prev.filter(p => p.id !== id));
          message.success('题目已删除');
        } catch (error) {
          console.error('Delete problem failed:', error);
          message.error('删除题目失败：' + (error.message || '未知错误'));
        }
      }
    });
  };

  const handleImport = async () => {
    try {
      const importedProblems = await importProblems();
      setProblems(prev => [...prev, ...importedProblems]);
      message.success('导入成功');
    } catch (error) {
      console.error('Import problems failed:', error);
      message.error('导入失败：' + (error.message || '未知错误'));
    }
  };

  const handleExport = async () => {
    try {
      await exportProblems(problems);
      message.success('导出成功');
    } catch (error) {
      console.error('Export problems failed:', error);
      message.error('导出失败：' + (error.message || '未知错误'));
    }
  };

  const columns = [
    {
      title: '题目名称',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/problems/edit/${record.id}`)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteProblem(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="settings">
      <Card title="默认题目设置" className="setting-card">
        <Select
          value={settings.default_problem_id}
          onChange={handleDefaultProblemChange}
          placeholder="请选择默认题目"
          style={{ width: 300 }}
        >
          {problems.map(problem => (
            <Select.Option key={problem.id} value={problem.id}>
              {problem.title}
            </Select.Option>
          ))}
        </Select>
      </Card>

      <Card
        title="题目管理"
        className="setting-card"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/problems/new')}
            >
              新建题目
            </Button>
            <Button
              icon={<ImportOutlined />}
              onClick={handleImport}
            >
              导入
            </Button>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExport}
            >
              导出
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={problems}
          rowKey="id"
          loading={loading}
        />
      </Card>

      <Card title="API Key 管理" className="setting-card">
        <Space>
          <Input.Password
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
            placeholder="请输入 DeepSeek API Key"
            style={{ width: 300 }}
          />
          <Button
            type="primary"
            onClick={handleApiKeyChange}
          >
            保存
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default Settings; 
