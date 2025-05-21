import unittest
from unittest.mock import patch, MagicMock
from app.services.judge0_service import Judge0Service

class TestJudge0Service(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_app = MagicMock()
        self.mock_app.config = {
            'JUDGE0_API_URL': 'http://localhost:2358',
            'JUDGE0_API_KEY': 'test_key'
        }
        self.mock_app.logger = MagicMock()
        
        # Patch current_app to return our mock
        self.current_app_patcher = patch('flask.current_app', self.mock_app)
        self.current_app_patcher.start()
        
        self.judge0_service = Judge0Service()

    def tearDown(self):
        """Clean up after each test method."""
        self.current_app_patcher.stop()

    @patch('requests.get')
    def test_get_languages(self, mock_get):
        """Test getting supported languages."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'id': 71, 'name': 'Python (3.8.0)'},
            {'id': 63, 'name': 'JavaScript (Node.js 12.14.0)'}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Test
        result = self.judge0_service.get_languages()
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 71)
        self.assertEqual(result[0]['name'], 'Python (3.8.0)')
        mock_get.assert_called_once_with(
            'http://localhost:2358/languages',
            headers={'Content-Type': 'application/json', 'X-RapidAPI-Key': 'test_key'},
            timeout=10
        )

    @patch('requests.post')
    def test_submit_code_python(self, mock_post):
        """Test submitting Python code."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'token': 'test_token'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Test
        result = self.judge0_service.submit_code(
            source_code='print("Hello")',
            language='python',
            stdin='test input'
        )

        # Assertions
        self.assertEqual(result, 'test_token')
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertEqual(call_args['headers'], {
            'Content-Type': 'application/json',
            'X-RapidAPI-Key': 'test_key'
        })
        self.assertEqual(call_args['json']['language_id'], 71)
        self.assertEqual(call_args['json']['source_code'], 'print("Hello")')
        self.assertEqual(call_args['json']['stdin'], 'test input')

    @patch('requests.get')
    def test_get_submission_details(self, mock_get):
        """Test getting submission details."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': {'id': 3, 'description': 'Accepted'},
            'stdout': 'Hello\n',
            'stderr': None
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Test
        result = self.judge0_service.get_submission_details('test_token')

        # Assertions
        self.assertEqual(result['status']['id'], 3)
        self.assertEqual(result['stdout'], 'Hello\n')
        mock_get.assert_called_once_with(
            'http://localhost:2358/submissions/test_token?base64_encoded=false&fields=*',
            headers={'Content-Type': 'application/json', 'X-RapidAPI-Key': 'test_key'},
            timeout=10
        )

    @patch('requests.get')
    def test_wait_for_submission(self, mock_get):
        """Test waiting for submission completion."""
        # Mock responses for multiple calls
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            'status': {'id': 2, 'description': 'Processing'}
        }
        mock_response1.raise_for_status = MagicMock()

        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            'status': {'id': 3, 'description': 'Accepted'},
            'stdout': 'Hello\n'
        }
        mock_response2.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_response1, mock_response2]

        # Test
        result = self.judge0_service.wait_for_submission('test_token', timeout_seconds=5, poll_interval=0.1)

        # Assertions
        self.assertEqual(result['status']['id'], 3)
        self.assertEqual(result['stdout'], 'Hello\n')
        self.assertEqual(mock_get.call_count, 2)

if __name__ == '__main__':
    unittest.main() 
