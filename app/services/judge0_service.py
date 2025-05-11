import requests
import time
from flask import current_app

class Judge0Service:
    def __init__(self):
        self.base_url = current_app.config.get('JUDGE0_API_URL') # e.g., 'http://localhost:2358'
        self.api_key = current_app.config.get('JUDGE0_API_KEY') # Optional, if Judge0 is secured
        self.headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            # Adjust header based on Judge0's authentication method if using an API key
            # For example, some might use 'X-Auth-Token' or 'Authorization: Bearer <token>'
            # self.headers['X-RapidAPI-Key'] = self.api_key # Example for RapidAPI hosted Judge0
            pass # Add appropriate auth header if needed

    def submit_code(self, source_code: str, language_id: int, stdin: str = None, expected_output: str = None, cpu_time_limit: float = 2.0, memory_limit: int = 128000):
        """
        Submits code to Judge0 for execution.

        :param source_code: The source code to execute.
        :param language_id: The Judge0 language ID (e.g., 71 for Python 3.8).
        :param stdin: Standard input for the code.
        :param expected_output: Expected standard output (for comparison).
        :param cpu_time_limit: CPU time limit in seconds.
        :param memory_limit: Memory limit in kilobytes.
        :return: The submission token from Judge0 or None if submission failed.
        """
        payload = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "expected_output": expected_output,
            "cpu_time_limit": cpu_time_limit,
            "memory_limit": memory_limit, # in kilobytes
            # "callback_url": "YOUR_CALLBACK_URL" # Optional: if you want Judge0 to notify your app
        }
        try:
            response = requests.post(f"{self.base_url}/submissions?base64_encoded=false&wait=false", json=payload, headers=self.headers, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json().get('token')
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Judge0 submission failed: {e}")
            return None

    def get_submission_details(self, token: str):
        """
        Retrieves the details of a submission from Judge0 using its token.

        :param token: The submission token.
        :return: The submission details as a dictionary or None if retrieval failed.
        """
        if not token:
            return None
        try:
            response = requests.get(f"{self.base_url}/submissions/{token}?base64_encoded=false&fields=*", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Judge0 get submission details failed for token {token}: {e}")
            return None

    def get_languages(self):
        """
        Retrieves the list of supported languages from Judge0.

        :return: A list of language objects or None if retrieval failed.
        """
        try:
            response = requests.get(f"{self.base_url}/languages", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Judge0 get languages failed: {e}")
            return None

    def get_system_info(self):
        """
        Retrieves system information from Judge0 (version, etc.).

        :return: System info as a dictionary or None if retrieval failed.
        """
        try:
            response = requests.get(f"{self.base_url}/system_info", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Judge0 get system info failed: {e}")
            return None

    def get_about_info(self):
        """
        Retrieves about information from Judge0.

        :return: About info as a dictionary or None if retrieval failed.
        """
        try:
            response = requests.get(f"{self.base_url}/about", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Judge0 get about info failed: {e}")
            return None

    def wait_for_submission(self, token: str, timeout_seconds: int = 60, poll_interval: int = 1):
        """
        Waits for a Judge0 submission to complete by polling its status.

        :param token: The submission token.
        :param timeout_seconds: Maximum time to wait for completion.
        :param poll_interval: Interval between status checks.
        :return: The final submission details or None if timed out or an error occurred.
        """
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            details = self.get_submission_details(token)
            if details:
                status_id = details.get('status', {}).get('id')
                # Status IDs: 1 (In Queue), 2 (Processing), 3 (Accepted), 4 (Wrong Answer), ...
                # See Judge0 documentation for all status IDs
                if status_id and status_id > 2: # Processing finished (either success or error)
                    return details
            else:
                # Error fetching details, likely a problem with Judge0 or network
                return None 
            time.sleep(poll_interval)
        current_app.logger.warning(f"Judge0 submission {token} timed out after {timeout_seconds} seconds.")
        return self.get_submission_details(token) # Return last known status

# Example Usage (for testing, typically this would be called from an API endpoint):
if __name__ == '__main__':
    # This example requires a running Flask app context for current_app.config
    # and a running Judge0 instance.
    # You would typically mock current_app or run this within a Flask shell.

    # Mock Flask app and config for standalone testing
    class MockApp:
        def __init__(self):
            self.config = {
                'JUDGE0_API_URL': 'http://localhost:2358', # Replace with your Judge0 URL
                'JUDGE0_API_KEY': None # Add your API key if Judge0 is secured
            }
            self.logger = MockLogger()

    class MockLogger:
        def error(self, msg):
            print(f"ERROR: {msg}")
        def warning(self, msg):
            print(f"WARNING: {msg}")
        def info(self, msg):
            print(f"INFO: {msg}")

    current_app = MockApp() # Mock current_app for this example

    judge0_service = Judge0Service()

    # 1. Get available languages
    print("Fetching languages...")
    languages = judge0_service.get_languages()
    if languages:
        print(f"Supported languages (first 5): {languages[:5]}")
        python_lang = next((lang for lang in languages if 'python' in lang['name'].lower() and '3' in lang['name']), None)
        if python_lang:
            print(f"Found Python 3: ID {python_lang['id']}, Name: {python_lang['name']}")
            python_lang_id = python_lang['id']

            # 2. Submit code
            sample_code = "print(input())"
            sample_stdin = "Hello Judge0"
            print(f"\nSubmitting Python code: {sample_code} with stdin: {sample_stdin}")
            submission_token = judge0_service.submit_code(source_code=sample_code, language_id=python_lang_id, stdin=sample_stdin)

            if submission_token:
                print(f"Submission successful. Token: {submission_token}")

                # 3. Wait for submission to complete and get details
                print("Waiting for submission to complete...")
                submission_details = judge0_service.wait_for_submission(submission_token)

                if submission_details:
                    print("\nSubmission details:")
                    print(f"  Status: {submission_details.get('status', {}).get('description')}")
                    print(f"  Time: {submission_details.get('time')}s")
                    print(f"  Memory: {submission_details.get('memory')}KB")
                    print(f"  Stdout: {submission_details.get('stdout')}")
                    print(f"  Stderr: {submission_details.get('stderr')}")
                    print(f"  Compile Output: {submission_details.get('compile_output')}")
                    print(f"  Message: {submission_details.get('message')}")
                else:
                    print("Failed to retrieve submission details or timed out.")
            else:
                print("Code submission failed.")
        else:
            print("Python 3 language not found in Judge0 languages.")
    else:
        print("Failed to fetch languages from Judge0.")

    # 4. Get system info
    print("\nFetching system info...")
    system_info = judge0_service.get_system_info()
    if system_info:
        print(f"Judge0 System Info: {system_info}")

    # 5. Get about info
    print("\nFetching about info...")
    about_info = judge0_service.get_about_info()
    if about_info:
        print(f"Judge0 About Info: {about_info}")
