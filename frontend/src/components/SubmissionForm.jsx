import React, { useState } from 'react';
import './SubmissionForm.css';

function SubmissionForm() {
    const [language, setLanguage] = useState('python');
    const [sourceCode, setSourceCode] = useState('');
    const [stdin, setStdin] = useState('');
    const [submissionResult, setSubmissionResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    const handleSubmit = async (event) => {
        event.preventDefault();
        setSubmissionResult(null); // Reset previous results
        setMessage({ text: '', type: '' }); // Clear previous messages
        setIsLoading(true);

        try {
            const response = await fetch('/api/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    language: language,
                    source_code: sourceCode, 
                    stdin: stdin 
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'API 请求失败，且无法解析错误响应。' }));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            setSubmissionResult(result);
            setMessage({ text: '代码已成功提交并评测！', type: 'success' });
            // alert('代码已成功提交并评测！'); // Removed alert

        } catch (error) {
            console.error('提交代码时出错:', error);
            setSubmissionResult({
                status_description: 'Error',
                time: '-',
                memory: '-',
                stdout: '-',
                stderr: error.message || '未知错误',
                compile_output: '-',
                error_message: error.message || '提交过程中发生客户端错误。'
            });
            setMessage({ text: `提交失败: ${error.message}`, type: 'error' });
            // alert(`提交失败: ${error.message}`); // Removed alert
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="submission-form-container">
            <h1>在线代码评测</h1>
            <form onSubmit={handleSubmit} id="code-submission-form">
                <div className="form-group">
                    <label htmlFor="language">选择语言:</label>
                    <select id="language" name="language" className="form-control" value={language} onChange={(e) => setLanguage(e.target.value)}>
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="java">Java</option>
                        <option value="c++">C++</option>
                        <option value="c">C</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="source_code">源代码:</label>
                    <textarea 
                        id="source_code" 
                        name="source_code" 
                        rows="15" 
                        className="form-control" 
                        placeholder="在此输入您的代码..." 
                        value={sourceCode} 
                        onChange={(e) => setSourceCode(e.target.value)}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="stdin">标准输入 (可选):</label>
                    <textarea 
                        id="stdin" 
                        name="stdin" 
                        rows="5" 
                        className="form-control" 
                        placeholder="如果您的代码需要输入，请在此处提供..." 
                        value={stdin} 
                        onChange={(e) => setStdin(e.target.value)}
                    />
                </div>

                <button type="submit" className="btn btn-primary" disabled={isLoading}>
                    {isLoading ? '正在提交...' : '提交代码'}
                </button>
            </form>

            {message.text && (
                <div className={`message-container ${message.type === 'success' ? 'message-success' : 'message-error'}`}>
                    {message.text}
                </div>
            )}

            {submissionResult && (
                <div id="result-container" style={{ marginTop: '20px' }}>
                    <h2>评测结果:</h2>
                    <div id="output-details">
                        <p><strong>状态:</strong> <span id="status-description">{submissionResult.status_description}</span></p>
                        <p><strong>时间 (ms):</strong> <span id="time-taken">{submissionResult.time}</span></p>
                        <p><strong>内存 (KB):</strong> <span id="memory-used">{submissionResult.memory}</span></p>
                        <p><strong>标准输出:</strong></p>
                        <pre id="stdout-output">{submissionResult.stdout || '-'}</pre>
                        <p><strong>标准错误:</strong></p>
                        <pre id="stderr-output">{submissionResult.stderr || '-'}</pre>
                        <p><strong>编译输出:</strong></p>
                        <pre id="compile-output">{submissionResult.compile_output || '-'}</pre>
                        <p><strong>错误信息:</strong></p>
                        <pre id="error-message">{submissionResult.error_message || '-'}</pre>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SubmissionForm;
