import requests
import time
from flask import current_app
from typing import Union, Dict, Any, Optional, List # Added Union, Dict, Any, Optional, List

# Default Judge0 Language IDs. It's recommended to fetch these dynamically using get_languages()
# for the specific Judge0 instance if possible, as IDs can vary.
# These are common IDs, ensure they match your Judge0 instance configuration.
# Python, JavaScript, Java, C++ as per PLAN.md 1.4.3.1
LANGUAGE_NAME_TO_ID_MAP: Dict[str, int] = {
    "python": 71,        # Python (3.8.0)
    "python3": 71,       # Alias for Python 3
    "javascript": 63,    # JavaScript (Node.js 12.14.0)
    "node.js": 63,       # Alias for JavaScript
    "java": 62,          # Java (OpenJDK 13.0.1)
    "c++": 54,           # C++ (GCC 9.2.0)
    "cpp": 54,           # Alias for C++
    "c": 50,             # C (GCC 9.2.0)
    # Add more languages and their corresponding Judge0 IDs as needed
    # From https://github.com/judge0/judge0 (Judge0 CE v1.13.1 list)
    # "python": 38, # Python (3.8.1)
    # "javascript_node": 26, # JavaScript (Node.js 12.14.0)
    # "java_openjdk_13": 25, # Java (OpenJDK 13.0.1)
    # "cpp_gcc_9": 12, # C++ (GCC 9.2.0)
}

class Judge0Service:
    def __init__(self):
        self.base_url = current_app.config.get('JUDGE0_API_URL') # e.g., 'http://localhost:2358'
        self.api_key = current_app.config.get('JUDGE0_API_KEY') # Optional, if Judge0 is secured
        self.headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            # Adjust header based on Judge0's authentication method if using an API key.
            # The specific header depends on the Judge0 instance's configuration.
            # Common examples include 'X-Auth-Token', 'Authorization: Bearer <token>',
            # or 'X-RapidAPI-Key' if using Judge0 via RapidAPI.
            # We'll use 'X-RapidAPI-Key' as per the existing comment example.
            # If your Judge0 instance uses a different auth mechanism, update this line.
            self.headers['X-RapidAPI-Key'] = self.api_key
            # Example for another common header:
            # self.headers['X-Auth-Token'] = self.api_key
            # Example for Bearer token:
            # self.headers['Authorization'] = f'Bearer {self.api_key}'

    def submit_code(self, source_code: str, language: Union[str, int], stdin: Optional[str] = None, expected_output: Optional[str] = None, cpu_time_limit: Optional[float] = None, memory_limit: Optional[int] = None) -> Optional[str]:
        """
        Submits code to Judge0 for execution.

        :param source_code: The source code to execute.
        :param language: The Judge0 language ID (e.g., 71) or language name (e.g., "python").
        :param stdin: Standard input for the code.
        :param expected_output: Expected standard output (for comparison).
        :param cpu_time_limit: Optional CPU time limit in seconds. Judge0 uses its default if None.
        :param memory_limit: Optional memory limit in kilobytes. Judge0 uses its default if None.
        :return: The submission token from Judge0 or None if submission failed.
        """
        actual_language_id: Optional[int] = None
        if isinstance(language, int):
            actual_language_id = language
        elif isinstance(language, str):
            actual_language_id = LANGUAGE_NAME_TO_ID_MAP.get(language.lower())
            if actual_language_id is None:
                current_app.logger.error(f"Unsupported language name: {language}. Please use a valid language ID or a mapped name.")
                # Optionally, try to fetch all languages and find a match
                # all_langs = self.get_languages()
                # if all_langs:
                #     found_lang = next((l.get('id') for l in all_langs if language.lower() in l.get('name', '').lower()), None)
                #     if found_lang:
                #         actual_language_id = found_lang
                #     else:
                #         return None
                # else:
                return None
        else:
            current_app.logger.error(f"Invalid language type: {type(language)}. Must be str or int.")
            return None

        payload: Dict[str, Any] = {
            "source_code": source_code,
            "language_id": actual_language_id,
            # "callback_url": "YOUR_CALLBACK_URL" # Optional: if you want Judge0 to notify your app
        }
        if stdin is not None:
            payload["stdin"] = stdin
        if expected_output is not None:
            payload["expected_output"] = expected_output
        if cpu_time_limit is not None:
            payload["cpu_time_limit"] = cpu_time_limit
        if memory_limit is not None:
            payload["memory_limit"] = memory_limit

        try:
            response = requests.post(f"{self.base_url}/submissions?base64_encoded=false&wait=false", json=payload, headers=self.headers, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json().get('token')
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Judge0 submission failed: {e}")
            return None

    def get_submission_details(self, token: str): # -> Optional[Dict[str, Any]] type hint can be added
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

    def get_languages(self): # -> Optional[List[Dict[str, Any]]] type hint can be added
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

    def get_system_info(self): # -> Optional[Dict[str, Any]] type hint can be added
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

    def get_about_info(self): # -> Optional[Dict[str, Any]] type hint can be added
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

    def wait_for_submission(self, token: str, timeout_seconds: int = 60, poll_interval: int = 1): # -> Optional[Dict[str, Any]]
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
                'JUDGE0_API_KEY': None, # Add your API key if Judge0 is secured
                'LOGGER_NAME': 'mock_logger' # Added for consistency if logger uses app.name
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
        # Example: Find Python language ID dynamically (more robust)
        # python_lang_dynamic = next((lang for lang in languages if 'python' in lang.get('name', '').lower() and '3.8' in lang.get('name', '')), None)
        # if python_lang_dynamic:
        #     python_lang_id_dynamic = python_lang_dynamic['id']
        #     print(f"Dynamically found Python 3.8: ID {python_lang_id_dynamic}, Name: {python_lang_dynamic['name']}")
        # else:
        #     print("Python 3.8 not found dynamically, using mapped ID.")

        # 2. Submit code using language name
        sample_code_python = "print(input())"
        sample_stdin_python = "Hello Python from Judge0"
        print(f"\nSubmitting Python code using name 'python': {sample_code_python} with stdin: {sample_stdin_python}")
        submission_token_python = judge0_service.submit_code(source_code=sample_code_python, language="python", stdin=sample_stdin_python)

        if submission_token_python:
            print(f"Python submission successful. Token: {submission_token_python}")
            print("Waiting for Python submission to complete...")
            submission_details_python = judge0_service.wait_for_submission(submission_token_python)
            if submission_details_python:
                print("\nPython submission details:")
                print(f"  Status: {submission_details_python.get('status', {}).get('description')}")
                print(f"  Stdout: {submission_details_python.get('stdout')}")
            else:
                print("Failed to retrieve Python submission details or timed out.")
        else:
            print("Python code submission failed.")

        # Example for C++
        sample_code_cpp = "#include <iostream>\nint main() { std::string s; std::cin >> s; std::cout << \"Hello C++: \" << s << std::endl; return 0; }"
        sample_stdin_cpp = "World"
        print(f"\nSubmitting C++ code using name 'c++': {sample_code_cpp} with stdin: {sample_stdin_cpp}")
        submission_token_cpp = judge0_service.submit_code(source_code=sample_code_cpp, language="c++", stdin=sample_stdin_cpp)

        if submission_token_cpp:
            print(f"C++ submission successful. Token: {submission_token_cpp}")
            print("Waiting for C++ submission to complete...")
            submission_details_cpp = judge0_service.wait_for_submission(submission_token_cpp)
            if submission_details_cpp:
                print("\nC++ submission details:")
                print(f"  Status: {submission_details_cpp.get('status', {}).get('description')}")
                print(f"  Stdout: {submission_details_cpp.get('stdout')}")
                if submission_details_cpp.get('stderr'):
                    print(f"  Stderr: {submission_details_cpp.get('stderr')}")
                if submission_details_cpp.get('compile_output'):
                    print(f"  Compile Output: {submission_details_cpp.get('compile_output')}")
            else:
                print("Failed to retrieve C++ submission details or timed out.")
        else:
            print("C++ code submission failed.")

    else:
        print("Failed to fetch languages. Cannot run detailed example.")

    # 3. Get system info (example)
    print("\nFetching system info...")
    system_info = judge0_service.get_system_info()
    if system_info:
        print(f"Judge0 System Info: {system_info}")

    # 5. Get about info
    print("\nFetching about info...")
    about_info = judge0_service.get_about_info()
    if about_info:
        print(f"Judge0 About Info: {about_info}")
