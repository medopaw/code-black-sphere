import React, { useState } from 'react';
import { Row, Col, Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import MDEditor from '@uiw/react-md-editor';
import { uploadImage } from '../../services/uploadService';
import './MarkdownEditor.css';

const { Dragger } = Upload;

const MarkdownEditor = ({ value, onChange }) => {
  const [preview, setPreview] = useState('edit');

  const handleImageUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await uploadImage(formData);
      const imageUrl = response.url;
      
      // 在光标位置插入图片链接
      const imageMarkdown = `![${file.name}](${imageUrl})`;
      onChange(value + '\n' + imageMarkdown);
      
      return false; // 阻止默认上传行为
    } catch (error) {
      message.error('图片上传失败');
      return false;
    }
  };

  return (
    <div className="markdown-editor">
      <div className="editor-toolbar">
        <Dragger
          accept="image/*"
          showUploadList={false}
          beforeUpload={handleImageUpload}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽图片到此处上传</p>
        </Dragger>
      </div>
      
      <Row gutter={16}>
        <Col span={preview === 'edit' ? 24 : 12}>
          <MDEditor
            value={value}
            onChange={onChange}
            preview={preview}
            height={500}
          />
        </Col>
        {preview === 'live' && (
          <Col span={12}>
            <div className="preview-container">
              <MDEditor.Markdown source={value} />
            </div>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default MarkdownEditor; 
