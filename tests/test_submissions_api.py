import unittest
import json
from app import create_app, db
from app.models import Candidate, Problem, TestCase, Submission, Setting
from unittest.mock import patch, MagicMock

class SubmissionsAPITestCase(unittest.TestCase):
    def setUp(self):
        from app.config import TestingConfig
        self.app = create_app(config_class=TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a candidate
        self.candidate = Candidate(name="Test Candidate", email="test@example.com")
        self.candidate.set_password("testpassword")
        db.session.add(self.candidate)
        db.session.commit()

        # Create a problem
        self.problem = Problem(title="Test Problem", description="A test problem.", llm_prompt="Review this code.")
        db.session.add(self.problem)
        db.session.commit()

        # Create a test case for the problem
        self.test_case1 = TestCase(
            problem_id=self.problem.id, 
            input_params=json.dumps("Hello"), 
            expected_output=json.dumps("Hello World")
        )
        self.test_case2 = TestCase(
            problem_id=self.problem.id, 
            input_params=json.dumps("Input2"), 
            expected_output=json.dumps("Output2")
        )
        db.session.add_all([self.test_case1, self.test_case2])
        db.session.commit()

        # Mock Judge0 API URL and LLM API Key for tests
        self.app.config['JUDGE0_API_URL'] = 'http://mockjudge0.com'
        # Add a setting for deepseek_api_key for llm_service to pick up
        setting = Setting(key='deepseek_api_key', value='test_deepseek_key')
        db.session.add(setting)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async') # Mock the async LLM call
    def test_submit_solution_success(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        # Mock Judge0 responses for two test cases
        mock_submit_code.side_effect = ['token1', 'token2'] # Tokens for two test cases
        mock_wait_for_submission.side_effect = [
            {
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': 'Hello World',
                'stderr': None,
                'compile_output': None,
                'time': '0.1',
                'memory': '1024'
            },
            {
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': 'Output2',
                'stderr': None,
                'compile_output': None,
                'time': '0.2',
                'memory': '2048'
            }
        ]
        mock_llm_review.return_value = None # Simulate async call, actual review not tested here

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Hello World")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertIn('submission', json_response)
        self.assertEqual(json_response['submission']['status'], 'Accepted')
        self.assertEqual(len(json_response['submission']['test_results']), 2)
        self.assertTrue(json_response['submission']['test_results'][0]['passed'])
        self.assertTrue(json_response['submission']['test_results'][1]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['output'], 'Hello World')
        self.assertEqual(json_response['submission']['test_results'][1]['output'], 'Output2')

        # Verify submission is in DB
        submission = Submission.query.get(json_response['submission']['id'])
        self.assertIsNotNone(submission)
        self.assertEqual(submission.status, 'Accepted')
        mock_llm_review.assert_called_once_with(submission.id)

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_wrong_answer(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.side_effect = ['token1_wa', 'token2_wa']
        mock_wait_for_submission.side_effect = [
            {
                'status': {'id': 3, 'description': 'Accepted'}, # Judge0 says accepted
                'stdout': 'Wrong Output',
                'stderr': None,
                'compile_output': None,
                'time': '0.1',
                'memory': '1024'
            },
            {
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': 'Output2', # Second one correct
                'stderr': None,
                'compile_output': None,
                'time': '0.1',
                'memory': '1024'
            }
        ]
        mock_llm_review.return_value = None

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Wrong Output")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Wrong Answer')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Wrong Answer')
        self.assertTrue(json_response['submission']['test_results'][1]['passed'])
        mock_llm_review.assert_not_called()

    def test_submit_solution_missing_fields(self):
        payload = {
            'candidate_id': self.candidate.id,
            # 'problem_id': self.problem.id, # Missing
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required fields', response.get_json()['message'])

    def test_submit_solution_invalid_language(self):
        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'unknownlang',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported language', response.get_json()['message'])

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_compile_error(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_compile_error'
        mock_wait_for_submission.return_value = {
            'status': {'id': 11, 'description': 'Compilation Error'},
            'stdout': None,
            'stderr': 'Compiler error message',
            'compile_output': 'Detailed compile error',
            'time': None,
            'memory': None
        }
        mock_llm_review.return_value = None

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'c++',
            'code': 'invalid c++ code'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Compilation Error')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Compilation Error')
        self.assertEqual(json_response['submission']['test_results'][0]['compile_output'], 'Detailed compile error')
        mock_llm_review.assert_not_called() # LLM review might not be called for compile errors

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_runtime_error(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_runtime_error'
        mock_wait_for_submission.return_value = {
            'status': {'id': 7, 'description': 'Runtime Error (SIGSEGV)'}, # Example runtime error
            'stdout': None,
            'stderr': 'Segmentation fault',
            'compile_output': None,
            'time': '0.05',
            'memory': '500'
        }
        mock_llm_review.return_value = None

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'import os; os.kill(os.getpid(), 9)' # Code causing runtime error
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Runtime Error (SIGSEGV)')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Runtime Error (SIGSEGV)')
        self.assertEqual(json_response['submission']['test_results'][0]['error'], 'Segmentation fault')
        mock_llm_review.assert_not_called()

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    def test_submit_solution_judge0_submit_fails(self, mock_submit_code):
        mock_submit_code.return_value = None # Simulate Judge0 submission failure

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("test")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201) # The API still creates a submission record
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Execution Error')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Failed to submit to Judge0')

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    def test_submit_solution_judge0_wait_fails(self, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_wait_fail'
        mock_wait_for_submission.return_value = None # Simulate Judge0 wait failure

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("test")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Execution Error')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Failed to retrieve execution results from Judge0')

    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_candidate_not_found(self, mock_llm_review):
        payload = {
            'candidate_id': 999,  # Non-existent candidate
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Candidate not found', response.get_json()['message'])
        mock_llm_review.assert_not_called()

    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_problem_not_found(self, mock_llm_review):
        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': 999,  # Non-existent problem
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Problem not found', response.get_json()['message'])
        mock_llm_review.assert_not_called()

    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_problem_no_test_cases(self, mock_llm_review):
        # Create a problem with no test cases
        problem_no_tc = Problem(title="Problem No TC", description="Desc", llm_prompt="Prompt")
        db.session.add(problem_no_tc)
        db.session.commit()

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': problem_no_tc.id,
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Problem has no test cases configured', response.get_json()['message'])
        mock_llm_review.assert_not_called()

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_judge0_submission_failure(self, mock_llm_review, mock_submit_code):
        mock_submit_code.return_value = None # Simulate failure to submit to Judge0

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201) # Still 201 as submission is created
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Execution Error')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Failed to submit to Judge0')
        mock_llm_review.assert_not_called() # LLM review should not be called for execution error

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_judge0_retrieval_failure(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_retrieval_fail'
        mock_wait_for_submission.return_value = None # Simulate failure to retrieve results

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Execution Error')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Failed to retrieve execution results from Judge0')
        mock_llm_review.assert_not_called()

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_time_limit_exceeded(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_tle'
        mock_wait_for_submission.return_value = {
            'status': {'id': 5, 'description': 'Time Limit Exceeded'},
            'stdout': None, 'stderr': 'TLE details', 'compile_output': None, 'time': '2.0', 'memory': '1024'
        }
        mock_llm_review.return_value = None

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'while True: pass'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Time Limit Exceeded')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Time Limit Exceeded')
        mock_llm_review.assert_not_called() # LLM review might not be called for TLE

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_memory_limit_exceeded(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_mle'
        mock_wait_for_submission.return_value = {
            'status': {'id': 6, 'description': 'Memory Limit Exceeded'},
            'stdout': None, 'stderr': 'MLE details', 'compile_output': None, 'time': '0.1', 'memory': '300000'
        }
        mock_llm_review.return_value = None

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'a = [0] * 10**8'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Memory Limit Exceeded')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertEqual(json_response['submission']['test_results'][0]['status_description'], 'Memory Limit Exceeded')
        mock_llm_review.assert_not_called() # LLM review might not be called for MLE

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_llm_review_not_triggered_for_execution_error(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.return_value = 'token_exec_error'
        mock_wait_for_submission.return_value = {
            'status': {'id': 11, 'description': 'Compilation Error'}, # Any non-successful execution
            'stdout': None, 'stderr': 'Error', 'compile_output': 'Error', 'time': None, 'memory': None
        }

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'syntax error code'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Compilation Error')
        mock_llm_review.assert_not_called()

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_with_custom_resource_limits(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        mock_submit_code.side_effect = ['token_custom_1', 'token_custom_2']
        mock_wait_for_submission.side_effect = [
            { # For self.test_case1
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': json.loads(self.test_case1.expected_output),
                'stderr': None,
                'compile_output': None,
                'time': '0.05',
                'memory': '500'
            },
            { # For self.test_case2
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': json.loads(self.test_case2.expected_output),
                'stderr': None,
                'compile_output': None,
                'time': '0.06',
                'memory': '512'
            }
        ]
        mock_llm_review.return_value = None

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Hello World")',
            'cpu_time_limit': 1.5,  # Custom CPU time limit
            'memory_limit': 100000 # Custom memory limit in KB
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Accepted')

        # Verify that submit_code was called with the custom limits for the first test case
        self.assertGreaterEqual(mock_submit_code.call_count, 1)
        first_call_args = mock_submit_code.call_args_list[0][1] # .call_args_list[0] is call_args object, [1] is kwargs
        self.assertEqual(first_call_args.get('source_code'), 'print("Hello World")')
        self.assertEqual(first_call_args.get('language'), 71)
        self.assertEqual(first_call_args.get('cpu_time_limit'), 1.5)
        self.assertEqual(first_call_args.get('memory_limit'), 100000)
        mock_llm_review.assert_called_once()

    @patch('app.services.judge0_service.Judge0Service.submit_code')
    @patch('app.services.judge0_service.Judge0Service.wait_for_submission')
    @patch('app.api.submissions.generate_llm_review_async')
    def test_submit_solution_invalid_test_case_json(self, mock_llm_review, mock_wait_for_submission, mock_submit_code):
        # Modify an existing test case to have invalid JSON
        original_input_params = self.test_case1.input_params
        self.test_case1.input_params = "invalid_json["
        db.session.add(self.test_case1)
        db.session.commit()

        # 设置 mock 返回值
        mock_submit_code.return_value = 'token_invalid_json'
        mock_wait_for_submission.return_value = {
            'status': {'id': 3, 'description': 'Accepted'},
            'stdout': 'Hello',
            'stderr': None,
            'compile_output': None,
            'time': '0.1',
            'memory': '1024'
        }

        payload = {
            'candidate_id': self.candidate.id,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("Hello")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertEqual(json_response['submission']['status'], 'Error in test case data')
        self.assertFalse(json_response['submission']['test_results'][0]['passed'])
        self.assertIn('Error in test case data', json_response['submission']['test_results'][0]['status_description'])
        self.assertIn('Could not parse JSON', json_response['submission']['test_results'][0]['error'])
        mock_llm_review.assert_not_called()

        # Restore original test case data
        self.test_case1.input_params = original_input_params
        db.session.add(self.test_case1)
        db.session.commit()

if __name__ == '__main__':
    unittest.main()
