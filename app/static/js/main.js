document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('code-submission-form');
    const submissionStatus = document.getElementById('submission-status');
    const resultContainer = document.getElementById('result-container');
    const outputDetails = document.getElementById('output-details');

    // Result fields
    const statusDescription = document.getElementById('status-description');
    const timeTaken = document.getElementById('time-taken');
    const memoryUsed = document.getElementById('memory-used');
    const stdoutOutput = document.getElementById('stdout-output');
    const stderrOutput = document.getElementById('stderr-output');
    const compileOutput = document.getElementById('compile-output');
    const errorMessage = document.getElementById('error-message');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        submissionStatus.textContent = '正在提交...';
        outputDetails.style.display = 'none'; // Hide previous results
        clearResultFields();

        const formData = new FormData(form);
        const data = {
            language: formData.get('language'),
            source_code: formData.get('source_code'),
            stdin: formData.get('stdin') || null,
            // expected_output: formData.get('expected_output') || null
        };

        try {
            const response = await fetch('/api/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.token) {
                submissionStatus.textContent = `提交成功！Token: ${result.token}. 正在等待结果...`;
                pollForResult(result.token);
            } else if (result.error) {
                submissionStatus.textContent = `提交失败: ${result.error}`;
                errorMessage.textContent = result.error;
                outputDetails.style.display = 'block';
            } else {
                submissionStatus.textContent = '提交失败，未收到 Token。';
                errorMessage.textContent = '未知提交错误。';
                outputDetails.style.display = 'block';
            }
        } catch (error) {
            console.error('提交错误:', error);
            submissionStatus.textContent = `提交出错: ${error.message}`;
            errorMessage.textContent = error.message;
            outputDetails.style.display = 'block';
        }
    });

    async function pollForResult(token) {
        const pollInterval = 2000; // Poll every 2 seconds
        const maxAttempts = 30; // Max 30 attempts (1 minute)
        let attempts = 0;

        const intervalId = setInterval(async () => {
            attempts++;
            if (attempts > maxAttempts) {
                clearInterval(intervalId);
                submissionStatus.textContent = `获取结果超时 (Token: ${token}). 请稍后手动检查。`;
                errorMessage.textContent = '获取结果超时。';
                outputDetails.style.display = 'block';
                return;
            }

            try {
                const response = await fetch(`/api/result/${token}`);
                if (!response.ok) {
                    // Handle non-200 responses during polling, but don't necessarily stop polling unless it's a fatal error
                    console.warn(`轮询 ${token} 时出错: ${response.status}`);
                    submissionStatus.textContent = `获取结果中... (尝试 ${attempts}/${maxAttempts}, 状态: ${response.status})`;
                    // If it's a 404, the token might be invalid or expired, so stop.
                    if (response.status === 404) {
                        clearInterval(intervalId);
                        submissionStatus.textContent = `获取结果失败: Token ${token} 无效或已过期。`;
                        errorMessage.textContent = `Token ${token} 无效或已过期。`;
                        outputDetails.style.display = 'block';
                    }
                    return; 
                }

                const resultData = await response.json();

                if (resultData) {
                    submissionStatus.textContent = `结果已获取 (Token: ${token})`;
                    outputDetails.style.display = 'block';
                    displayResults(resultData);

                    // Judge0 status IDs: 1 (In Queue), 2 (Processing)
                    // Any status > 2 means it's completed (Accepted, WA, TLE, CE, RTE etc.)
                    if (resultData.status && resultData.status.id > 2) {
                        clearInterval(intervalId);
                    } else {
                         submissionStatus.textContent = `正在处理 (Token: ${token}, 状态: ${resultData.status.description})... (尝试 ${attempts}/${maxAttempts})`;
                    }
                } else {
                    submissionStatus.textContent = `获取结果中... (尝试 ${attempts}/${maxAttempts}, 未收到有效数据)`;
                }
            } catch (error) {
                console.error('轮询错误:', error);
                // Don't stop polling on network errors, allow retries
                submissionStatus.textContent = `轮询时发生错误: ${error.message}. 正在重试... (尝试 ${attempts}/${maxAttempts})`;
            }
        }, pollInterval);
    }

    function displayResults(data) {
        statusDescription.textContent = data.status?.description || 'N/A';
        timeTaken.textContent = data.time !== null ? (parseFloat(data.time) * 1000).toFixed(2) : 'N/A'; // Assuming time is in seconds
        memoryUsed.textContent = data.memory !== null ? data.memory : 'N/A'; // Assuming memory is in KB
        stdoutOutput.textContent = data.stdout || '-';
        stderrOutput.textContent = data.stderr || '-';
        compileOutput.textContent = data.compile_output || '-';
        errorMessage.textContent = data.message || (data.status?.id > 3 ? data.status?.description : '-'); // Show status description as error if it's an error status
    }

    function clearResultFields() {
        statusDescription.textContent = '-';
        timeTaken.textContent = '-';
        memoryUsed.textContent = '-';
        stdoutOutput.textContent = '-';
        stderrOutput.textContent = '-';
        compileOutput.textContent = '-';
        errorMessage.textContent = '-';
    }
});
