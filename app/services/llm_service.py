from flask import current_app
import requests
import json
import time
from app.models import Setting, Problem, Submission # Assuming Submission will be updated here
from app import db # For potential async task updates

# It's good practice to define constants for setting keys
DEEPSEEK_API_KEY_SETTING = 'deepseek_api_key'
DEFAULT_LLM_MODEL = 'deepseek-coder' # Or whatever model is preferred

class LLMService:
    def __init__(self):
        self.api_key = self._get_api_key()
        self.base_url = current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com') # Or your specific endpoint

    def _get_api_key(self):
        # Fetch API key from database settings
        # Note: In a real app, API keys should be encrypted in the DB and decrypted here.
        # For simplicity, we assume it's stored as plain text for now, as per PLAN.md 1.3.6.3 note on encryption.
        api_key_setting = Setting.query.get(DEEPSEEK_API_KEY_SETTING)
        if api_key_setting and api_key_setting.value:
            return api_key_setting.value
        current_app.logger.warning(f'{DEEPSEEK_API_KEY_SETTING} not found in settings.')
        return None

    def get_llm_prompt_for_problem(self, problem_id: int) -> str:
        problem = Problem.query.get(problem_id)
        if problem and problem.llm_prompt:
            return problem.llm_prompt
        # Fallback to a generic prompt if specific one not found or problem doesn't exist
        current_app.logger.warning(f"LLM prompt for problem_id {problem_id} not found. Using generic prompt.")
        return "Please review the following code for its quality, correctness, efficiency, and provide suggestions for improvement. Score the code out of 100."

    def generate_review(self, code: str, problem_id: int, language: str, stream: bool = False) -> str:
        if not self.api_key:
            current_app.logger.error("DeepSeek API key is not configured. Cannot generate LLM review.")
            return "Error: LLM API key not configured."

        llm_prompt_template = self.get_llm_prompt_for_problem(problem_id)
        
        # Construct the prompt. You might want to make this more sophisticated.
        # Example: Include language, problem description, etc.
        # For now, just combining the template with the code.
        # Ensure the prompt clearly asks for what you need (review, suggestions, score).
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
            'stream': stream # Enable or disable streaming based on parameter
        }

        try:
            # Using v1/chat/completions endpoint as it's common for DeepSeek-like APIs
            max_retries = 3
            retry_delay = 5 # seconds
            response = None # Initialize response to None
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f'{self.base_url}/v1/chat/completions', 
                        headers=headers, 
                        json=payload, 
                        stream=stream, 
                        timeout=120 # Increased timeout for LLM
                    )
                    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                    break # If successful, exit retry loop
                except requests.exceptions.RequestException as e_req:
                    current_app.logger.warning(f"LLM API request attempt {attempt + 1}/{max_retries} failed: {e_req}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        # This was the last attempt, re-raise the exception or handle as final failure
                        raise # Re-raise the last exception to be caught by the outer try-except
            
            if response is None: # Should not happen if raise is used above, but as a safeguard
                current_app.logger.error("LLM API request failed after all retries, response is None.")
                return "Error: LLM API request failed after all retries."

            if stream:
                # 优化流式处理逻辑
                full_response_content = ""
                buffer = ""
                for chunk in response.iter_lines():
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        if decoded_chunk.startswith('data: '):
                            json_data_str = decoded_chunk[len('data: '):]
                            if json_data_str.strip() == "[DONE]":
                                # 处理缓冲区中的最后内容
                                if buffer:
                                    full_response_content += buffer
                                break
                            try:
                                json_data = json.loads(json_data_str)
                                if json_data['choices'][0]['delta'].get('content'):
                                    content = json_data['choices'][0]['delta']['content']
                                    buffer += content
                                    # 当缓冲区达到一定大小时，将其添加到完整响应中
                                    if len(buffer) >= 100:  # 可以根据需要调整缓冲区大小
                                        full_response_content += buffer
                                        buffer = ""
                            except json.JSONDecodeError as e:
                                current_app.logger.error(f"Error decoding stream chunk: {json_data_str}, error: {e}")
                                continue
                            except KeyError as e:
                                current_app.logger.error(f"Unexpected response structure: {json_data}, error: {e}")
                                continue
                return full_response_content.strip()
            else:
                response_data = response.json()
                # Extract the content from the response, structure may vary by LLM API
                # Assuming a common structure like response_data['choices'][0]['message']['content']
                if response_data.get('choices') and len(response_data['choices']) > 0:
                    message = response_data['choices'][0].get('message')
                    if message and message.get('content'):
                        return message['content'].strip()
                current_app.logger.error(f"Unexpected LLM API response structure: {response_data}")
                return "Error: Could not parse LLM response."

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"LLM API request failed: {e}")
            return f"Error: LLM API request failed - {e}"
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during LLM review generation: {e}")
            return f"Error: An unexpected error occurred - {e}"

# Example of how this might be called asynchronously (e.g., with Celery or Flask-APScheduler)
# This is a conceptual placeholder and would need a proper task queue setup.
def generate_llm_review_async(submission_id: int):
    from app import create_app # To get app context in a background task
    app = create_app()
    with app.app_context():
        submission = Submission.query.get(submission_id)
        if not submission:
            current_app.logger.error(f"Submission {submission_id} not found for async LLM review.")
            return

        if submission.llm_review: # Avoid re-processing if already done
            current_app.logger.info(f"LLM review for submission {submission_id} already exists.")
            return

        llm_service = LLMService()
        review_content = llm_service.generate_review(
            code=submission.code,
            problem_id=submission.problem_id,
            language=submission.language,
            stream=False # For background tasks, streaming to DB isn't typical directly
        )

        submission.llm_review = review_content
        try:
            db.session.commit()
            current_app.logger.info(f"LLM review for submission {submission_id} completed and saved.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to save LLM review for submission {submission_id}: {e}")

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
