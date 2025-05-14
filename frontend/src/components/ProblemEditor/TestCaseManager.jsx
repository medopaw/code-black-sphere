import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ImportOutlined, ExportOutlined } from '@ant-design/icons';
import { importTestCases, exportTestCases } from '../../services/testCaseService';
import './TestCaseManager.css';

const TestCaseManager = ({ testCases, onChange }) => {
  const [form] = Form.useForm();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState(null);

  const columns = [
    {
      title: '输入参数',
      dataIndex: 'input_params',
      key: 'input_params',
      render: (text) => (
        <pre className="json-display">{JSON.stringify(JSON.parse(text), null, 2)}</pre>
      ),
    },
    {
      title: '预期输出',
      dataIndex: 'expected_output',
      key: 'expected_output',
      render: (text) => (
        <pre className="json-display">{JSON.stringify(JSON.parse(text), null, 2)}</pre>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const handleAdd = () => {
    setEditingTestCase(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingTestCase(record);
    form.setFieldsValue({
      input_params: JSON.stringify(JSON.parse(record.input_params), null, 2),
      expected_output: JSON.stringify(JSON.parse(record.expected_output), null, 2),
    });
    setIsModalVisible(true);
  };

  const handleDelete = (record) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个测试用例吗？',
      onOk: () => {
        const newTestCases = testCases.filter(tc => tc.id !== record.id);
        onChange(newTestCases);
      },
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const newTestCase = {
        id: editingTestCase?.id || Date.now().toString(),
        input_params: values.input_params,
        expected_output: values.expected_output,
      };

      let newTestCases;
      if (editingTestCase) {
        newTestCases = testCases.map(tc =>
          tc.id === editingTestCase.id ? newTestCase : tc
        );
      } else {
        newTestCases = [...testCases, newTestCase];
      }

      onChange(newTestCases);
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
      message.error('表单验证失败，请检查输入');
    }
  };

  const handleImport = async () => {
    try {
      const file = await importTestCases();
      const newTestCases = [...testCases, ...file];
      onChange(newTestCases);
      message.success('导入成功');
    } catch (error) {
      console.error('Import failed:', error);
      message.error('导入失败：' + (error.message || '未知错误'));
    }
  };

  const handleExport = async () => {
    try {
      await exportTestCases(testCases);
      message.success('导出成功');
    } catch (error) {
      console.error('Export failed:', error);
      message.error('导出失败：' + (error.message || '未知错误'));
    }
  };

  return (
    <div className="test-case-manager">
      <div className="toolbar">
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加测试用例
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
      </div>

      <Table
        columns={columns}
        dataSource={testCases}
        rowKey="id"
        pagination={false}
      />

      <Modal
        title={editingTestCase ? '编辑测试用例' : '添加测试用例'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="input_params"
            label="输入参数 (JSON)"
            rules={[
              { required: true, message: '请输入输入参数' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch (error) {
                    return Promise.reject('请输入有效的 JSON');
                  }
                },
              },
            ]}
          >
            <Input.TextArea
              rows={6}
              placeholder='{"param1": "value1", "param2": "value2"}'
            />
          </Form.Item>

          <Form.Item
            name="expected_output"
            label="预期输出 (JSON)"
            rules={[
              { required: true, message: '请输入预期输出' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch (error) {
                    return Promise.reject('请输入有效的 JSON');
                  }
                },
              },
            ]}
          >
            <Input.TextArea
              rows={4}
              placeholder='"expected result" 或 {"key": "value"}'
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TestCaseManager; 
