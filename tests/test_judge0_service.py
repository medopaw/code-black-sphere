import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
import requests
from app.services.judge0_service import Judge0Service, LANGUAGE_NAME_TO_ID_MAP

class TestJudge0Service(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update({
            'JUDGE0_API_URL': 'http://localhost:2358',
            'JUDGE0_API_KEY': 'test_key'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.service = Judge0Service()

    def tearDown(self):
        self.app_context.pop()

    def test_init(self):
        """Test Judge0Service initialization"""
        self.assertEqual(self.service.base_url, 'http://localhost:2358')
        self.assertEqual(self.service.api_key, 'test_key')
        self.assertEqual(self.service.headers['Content-Type'], 'application/json')
        self.assertEqual(self.service.headers['X-RapidAPI-Key'], 'test_key')

    @patch('requests.post')
    def test_submit_code_success(self, mock_post):
        """Test successful code submission"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'token': 'test_token'}
        mock_post.return_value = mock_response

        result = self.service.submit_code(
            source_code='print("Hello")',
            language='python',
            stdin='test input',
            expected_output='Hello',
            cpu_time_limit=1.0,
            memory_limit=128
        )

        self.assertEqual(result, 'test_token')
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertEqual(call_args['json']['language_id'], LANGUAGE_NAME_TO_ID_MAP['python'])
        self.assertEqual(call_args['json']['source_code'], 'print("Hello")')
        self.assertEqual(call_args['json']['stdin'], 'test input')
        self.assertEqual(call_args['json']['expected_output'], 'Hello')
        self.assertEqual(call_args['json']['cpu_time_limit'], 1.0)
        self.assertEqual(call_args['json']['memory_limit'], 128)

    @patch('requests.post')
    def test_submit_code_invalid_language(self, mock_post):
        """Test code submission with invalid language"""
        result = self.service.submit_code(
            source_code='print("Hello")',
            language='invalid_language'
        )
        self.assertIsNone(result)
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_submit_code_request_error(self, mock_post):
        """Test code submission with request error"""
        mock_post.side_effect = requests.exceptions.RequestException('Network error')
        result = self.service.submit_code(
            source_code='print("Hello")',
            language='python'
        )
        self.assertIsNone(result)

    @patch('requests.get')
    def test_get_submission_details_success(self, mock_get):
        """Test successful submission details retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': {'id': 3, 'description': 'Accepted'},
            'stdout': 'Hello',
            'stderr': None,
            'compile_output': None
        }
        mock_get.return_value = mock_response

        result = self.service.get_submission_details('test_token')

        self.assertEqual(result['status']['id'], 3)
        self.assertEqual(result['stdout'], 'Hello')
        mock_get.assert_called_once_with(
            'http://localhost:2358/submissions/test_token?base64_encoded=false&fields=*',
            headers=self.service.headers,
            timeout=10
        )

    @patch('requests.get')
    def test_get_submission_details_request_error(self, mock_get):
        """Test submission details retrieval with request error"""
        mock_get.side_effect = requests.exceptions.RequestException('Network error')
        result = self.service.get_submission_details('test_token')
        self.assertIsNone(result)

    @patch('requests.get')
    def test_get_languages_success(self, mock_get):
        """Test successful languages retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'id': 71, 'name': 'Python (3.8.0)'},
            {'id': 63, 'name': 'JavaScript (Node.js 12.14.0)'}
        ]
        mock_get.return_value = mock_response

        result = self.service.get_languages()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 71)
        self.assertEqual(result[1]['id'], 63)
        mock_get.assert_called_once_with(
            'http://localhost:2358/languages',
            headers=self.service.headers,
            timeout=10
        )

    @patch('requests.get')
    def test_get_system_info_success(self, mock_get):
        """Test successful system info retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'version': '1.13.1',
            'status': 'running'
        }
        mock_get.return_value = mock_response

        result = self.service.get_system_info()

        self.assertEqual(result['version'], '1.13.1')
        self.assertEqual(result['status'], 'running')
        mock_get.assert_called_once_with(
            'http://localhost:2358/system_info',
            headers=self.service.headers,
            timeout=10
        )

    @patch('requests.get')
    def test_get_about_info_success(self, mock_get):
        """Test successful about info retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'name': 'Judge0',
            'description': 'Online code execution system'
        }
        mock_get.return_value = mock_response

        result = self.service.get_about_info()

        self.assertEqual(result['name'], 'Judge0')
        self.assertEqual(result['description'], 'Online code execution system')
        mock_get.assert_called_once_with(
            'http://localhost:2358/about',
            headers=self.service.headers,
            timeout=10
        )

    @patch('app.services.judge0_service.Judge0Service.get_submission_details')
    def test_wait_for_submission_success(self, mock_get_details):
        """Test successful submission wait"""
        # Mock the submission details to simulate a completed submission
        mock_get_details.return_value = {
            'status': {'id': 3, 'description': 'Accepted'},
            'stdout': 'Hello',
            'stderr': None
        }

        result = self.service.wait_for_submission('test_token', timeout_seconds=5, poll_interval=1)

        self.assertEqual(result['status']['id'], 3)
        self.assertEqual(result['stdout'], 'Hello')
        mock_get_details.assert_called_once()

    @patch('app.services.judge0_service.Judge0Service.get_submission_details')
    def test_wait_for_submission_timeout(self, mock_get_details):
        """Test submission wait timeout"""
        # Mock the submission details to simulate a processing submission
        mock_get_details.return_value = {
            'status': {'id': 2, 'description': 'Processing'}
        }

        result = self.service.wait_for_submission('test_token', timeout_seconds=1, poll_interval=0.5)

        self.assertEqual(result['status']['id'], 2)
        self.assertEqual(mock_get_details.call_count, 3)  # Initial + 2 polls

if __name__ == '__main__':
    unittest.main() 
