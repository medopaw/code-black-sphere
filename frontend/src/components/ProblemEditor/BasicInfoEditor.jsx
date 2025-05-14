import React from 'react';
import { Form, Input, Select, Space } from 'antd';

const { Option } = Select;

const DIFFICULTY_LEVELS = [
  { value: 'easy', label: '简单' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' }
];

const CATEGORIES = [
  { value: 'algorithm', label: '算法' },
  { value: 'data-structure', label: '数据结构' },
  { value: 'system-design', label: '系统设计' },
  { value: 'database', label: '数据库' },
  { value: 'network', label: '网络' }
];

const BasicInfoEditor = ({ problem, onChange }) => {
  const handleChange = (field, value) => {
    onChange(field, value);
  };

  return (
    <Form layout="vertical">
      <Form.Item
        label="题目名称"
        required
        rules={[{ required: true, message: '请输入题目名称' }]}
      >
        <Input
          value={problem.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="请输入题目名称"
        />
      </Form.Item>

      <Form.Item label="难度">
        <Select
          value={problem.difficulty}
          onChange={(value) => handleChange('difficulty', value)}
          placeholder="请选择难度"
        >
          {DIFFICULTY_LEVELS.map(level => (
            <Option key={level.value} value={level.value}>
              {level.label}
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item label="分类">
        <Select
          mode="multiple"
          value={problem.categories}
          onChange={(value) => handleChange('categories', value)}
          placeholder="请选择分类"
        >
          {CATEGORIES.map(category => (
            <Option key={category.value} value={category.value}>
              {category.label}
            </Option>
          ))}
        </Select>
      </Form.Item>
    </Form>
  );
};

export default BasicInfoEditor; 
