import React from 'react';
import { Box, Button, FormControl, InputLabel, Select, MenuItem, CircularProgress } from '@mui/material';
import Editor from '@monaco-editor/react';

const SUPPORTED_LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
];

const CodeEditor = ({ code, onChange, onSubmit, language, submitting }) => {
  const handleEditorChange = (value) => {
    onChange(value);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>编程语言</InputLabel>
          <Select
            value={language}
            label="编程语言"
            disabled={submitting}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <MenuItem key={lang.value} value={lang.value}>
                {lang.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          variant="contained"
          color="primary"
          onClick={onSubmit}
          disabled={submitting}
          sx={{ ml: 'auto', minWidth: 120 }}
        >
          {submitting ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
              评测中...
            </>
          ) : (
            '运行测试并评估'
          )}
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, border: '1px solid #ccc' }}>
        <Editor
          height="100%"
          defaultLanguage={language}
          value={code}
          onChange={handleEditorChange}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            readOnly: submitting,
          }}
        />
      </Box>
    </Box>
  );
};

export default CodeEditor; 
