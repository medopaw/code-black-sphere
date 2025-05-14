from flask import current_app
import requests
import json
import time
from app.models import Setting, Problem, Submission
from app import db
from typing import Optional, Dict, Any, Union
from requests.exceptions import RequestException, Timeout, ConnectionError
import logging

# 定义常量
DEEPSEEK_API_KEY_SETTING = 'deepseek_api_key'
DEFAULT_LLM_MODEL = 'deepseek-coder'
REQUEST_TIMEOUT = 120  # 秒
STREAM_BUFFER_SIZE = 100  # 字符

class LLMServiceError(Exception):
    """LLM 服务基础异常类"""
    pass

class LLMConfigError(LLMServiceError):
    """配置相关错误"""
    pass

class LLMAPIError(LLMServiceError):
    """API 调用相关错误"""
    pass

class LLMResponseError(LLMServiceError):
    """响应解析相关错误"""
    pass

class LLMTimeoutError(LLMServiceError):
    """超时相关错误"""
    pass

class LLMService:
    def __init__(self):
        self.api_key = self._get_api_key()
        self.base_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com')
        self.logger = logging.getLogger(__name__)

    def _get_api_key(self) -> Optional[str]:
        """获取 API Key，如果未配置则抛出异常"""
        api_key_setting = Setting.query.get(DEEPSEEK_API_KEY_SETTING)
        if not api_key_setting or not api_key_setting.value:
            raise LLMConfigError(f"{DEEPSEEK_API_KEY_SETTING} not found in settings")
        return api_key_setting.value

    def get_llm_prompt_for_problem(self, problem_id: int) -> str:
        """获取题目的 LLM Prompt，如果未找到则使用默认值"""
        problem = Problem.query.get(problem_id)
        if not problem:
            raise LLMConfigError(f"Problem with ID {problem_id} not found")
        
        if not problem.llm_prompt:
            self.logger.warning(f"LLM prompt for problem_id {problem_id} not found. Using generic prompt.")
            return "Please review the following code for its quality, correctness, efficiency, and provide suggestions for improvement. Score the code out of 100."
        
        return problem.llm_prompt

        reraise=True
    )
    def _make_api_request(self, headers: Dict[str, str], payload: Dict[str, Any], stream: bool = False) -> requests.Response:
        """发送 API 请求"""
        try:
            response = requests.post(
                f'{self.base_url}/v1/chat/completions',
                headers=headers,
                json=payload,
                stream=stream,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response
        except Timeout:
            self.logger.error("LLM API request timed out")
            raise LLMTimeoutError("Request to LLM API timed out")
        except ConnectionError:
            self.logger.error("Failed to connect to LLM API")
            raise LLMAPIError("Failed to connect to LLM API")
        except RequestException as e:
            self.logger.error(f"LLM API request failed: {str(e)}")
            raise LLMAPIError(f"LLM API request failed: {str(e)}")

    def _validate_response(self, response_data: Dict[str, Any]) -> str:
        """验证并解析 API 响应"""
        try:
            if not response_data.get('choices'):
                raise LLMResponseError("No choices in LLM response")
            
            if not response_data['choices'][0].get('message'):
                raise LLMResponseError("No message in LLM response choice")
            
            content = response_data['choices'][0]['message'].get('content')
            if not content:
                raise LLMResponseError("No content in LLM response message")
            
            # 验证内容长度
            if len(content.strip()) < 10:  # 假设有效响应至少需要10个字符
                raise LLMResponseError("LLM response content too short")
            
            return content.strip()
        except (KeyError, TypeError) as e:
            raise LLMResponseError(f"Invalid response format: {str(e)}")

    def _handle_stream_error(self, chunk: str, error: Exception) -> None:
        """处理流式响应错误"""
        self.logger.error(f"Error processing stream chunk: {chunk}, error: {str(error)}")
        raise LLMResponseError(f"Error processing stream response: {str(error)}")

    def generate_review(self, code: str, problem_id: int, language: str, stream: bool = False) -> str:
        """生成代码评审"""
        try:
            llm_prompt_template = self.get_llm_prompt_for_problem(problem_id)
            final_prompt = f"{llm_prompt_template}\n\nLanguage: {language}\n\nCode to review:\n```\n{code}\n```"

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': current_app.config.get('LLM_MODEL', DEFAULT_LLM_MODEL),
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful AI assistant that reviews code.'},
                    {'role': 'user', 'content': final_prompt}
                ],
                'stream': stream
            }

            try:
                response = self._make_api_request(headers, payload, stream)
            except (LLMAPIError, LLMTimeoutError) as e:
                self.logger.error(f"LLM API request failed after retries: {str(e)}")
                raise

            if stream:
                return self._handle_stream_response(response)
            else:
                return self._validate_response(response.json())

        except LLMConfigError as e:
            self.logger.error(f"LLM configuration error: {str(e)}")
            raise
        except LLMAPIError as e:
            self.logger.error(f"LLM API error: {str(e)}")
            raise
        except LLMResponseError as e:
            self.logger.error(f"LLM response error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in LLM review generation: {str(e)}")
            raise LLMServiceError(f"Unexpected error: {str(e)}")

    def _handle_stream_response(self, response: requests.Response) -> str:
        """处理流式响应"""
        full_response_content = ""
        buffer = ""
        start_time = time.time()
        
        try:
            for chunk in response.iter_lines():
                if time.time() - start_time > REQUEST_TIMEOUT:
                    raise LLMTimeoutError("Stream response timeout")

                if not chunk:
                    continue
                    
                decoded_chunk = chunk.decode('utf-8')
                if decoded_chunk.startswith('data: '):
                    json_data_str = decoded_chunk[len('data: '):]
                    
                    if json_data_str.strip() == "[DONE]":
                        if buffer:
                            full_response_content += buffer
                        break
                        
                    try:
                        json_data = json.loads(json_data_str)
                        if json_data['choices'][0]['delta'].get('content'):
                            content = json_data['choices'][0]['delta']['content']
                            buffer += content
                            
                            if len(buffer) >= STREAM_BUFFER_SIZE:
                                full_response_content += buffer
                                buffer = ""
                    except json.JSONDecodeError as e:
                        self._handle_stream_error(json_data_str, e)
                    except KeyError as e:
                        self._handle_stream_error(json_data_str, e)
                        
            if not full_response_content.strip():
                raise LLMResponseError("Empty response from LLM")
                
            return full_response_content.strip()
            
        except Exception as e:
            self.logger.error(f"Error processing stream response: {str(e)}")
            raise LLMResponseError(f"Stream processing error: {str(e)}")

def generate_llm_review_async(submission_id: int) -> None:
    """异步生成 LLM 评审"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        try:
            submission = Submission.query.get(submission_id)
            if not submission:
                current_app.logger.error(f"Submission {submission_id} not found for async LLM review")
                return

            if submission.llm_review:
                current_app.logger.info(f"LLM review for submission {submission_id} already exists")
                return

            llm_service = LLMService()
            review_content = llm_service.generate_review(
                code=submission.code,
                problem_id=submission.problem_id,
                language=submission.language,
                stream=False
            )

            submission.llm_review = review_content
            try:
                db.session.commit()
                current_app.logger.info(f"LLM review for submission {submission_id} completed and saved")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Failed to save LLM review for submission {submission_id}: {str(e)}")
                raise
                
        except LLMServiceError as e:
            current_app.logger.error(f"LLM service error for submission {submission_id}: {str(e)}")
            # 将错误信息保存到 submission 中
            if submission:
                submission.llm_review = f"Error generating review: {str(e)}"
                try:
                    db.session.commit()
                except Exception as db_error:
                    db.session.rollback()
                    current_app.logger.error(f"Failed to save error message for submission {submission_id}: {str(db_error)}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error in async LLM review for submission {submission_id}: {str(e)}")
            if submission:
                submission.llm_review = f"Unexpected error: {str(e)}"
                try:
                    db.session.commit()
                except Exception as db_error:
                    db.session.rollback()
                    current_app.logger.error(f"Failed to save error message for submission {submission_id}: {str(db_error)}")

if __name__ == '__main__':
    # This part is for conceptual testing and would require a Flask app context.
    # To run this standalone, you'd mock current_app, db, models, etc.
    class MockApp:
        def __init__(self):
            self.config = {
                'DEEPSEEK_API_URL': 'https://api.deepseek.com',
                'LLM_MODEL': 'deepseek-coder',
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:' # For mock DB
            }
            self.logger = MockLogger()

    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")

    # current_app = MockApp() # This would be needed for standalone execution
    # db.create_all() # If using a real DB for testing

    # Example usage (conceptual):
    # llm_service = LLMService()
    # test_code = "def hello():\n  print('Hello, world!')"
    # review = llm_service.generate_review(test_code, problem_id=1, language='python')
    # print(f"LLM Review: {review}")
    pass
