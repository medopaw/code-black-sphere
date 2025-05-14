import unittest
import json
from app import create_app, db
from app.config import TestingConfig as Config
from app.models import Problem, TestCase, Candidate

class TestCasesAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=Config) # Will now use TestingConfig as Config
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a problem to associate test cases with
        self.problem = Problem(title="Problem for TestCases", description="A problem.")
        db.session.add(self.problem)
        db.session.commit()

        # Initial test case for this problem
        self.test_case1 = TestCase(
            problem_id=self.problem.id,
            input_params=json.dumps({'param1': 'value1'}),
            expected_output=json.dumps('expected1')
        )
        db.session.add(self.test_case1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_test_case_success(self):
        payload = {
            'input_params': json.dumps({'param2': 'value2'}),
            'expected_output': json.dumps('expected2')
        }
        response = self.client.post(f'/api/problems/{self.problem.id}/testcases', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertIn('test_case', json_response)
        self.assertEqual(json.loads(json_response['test_case']['input_params']), {'param2': 'value2'})
        self.assertEqual(json.loads(json_response['test_case']['expected_output']), 'expected2')

        # Verify in DB
        tc = TestCase.query.get(json_response['test_case']['id'])
        self.assertIsNotNone(tc)
        self.assertEqual(tc.problem_id, self.problem.id)

    def test_create_test_case_for_nonexistent_problem(self):
        payload = {
            'input_params': json.dumps({'param': 'val'}),
            'expected_output': json.dumps('exp')
        }
        response = self.client.post('/api/problems/999/testcases', json=payload) # Non-existent problem ID
        self.assertEqual(response.status_code, 404)
        self.assertIn('Problem not found', response.get_json()['message'])

    def test_create_test_case_missing_fields(self):
        payload = {'input_params': json.dumps({'param': 'val'})} # Missing expected_output
        response = self.client.post(f'/api/problems/{self.problem.id}/testcases', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required fields', response.get_json()['message'])

    def test_get_all_test_cases_for_problem(self):
        # Add another test case
        tc2 = TestCase(problem_id=self.problem.id, input_params='{}', expected_output='{}')
        db.session.add(tc2)
        db.session.commit()

        response = self.client.get(f'/api/problems/{self.problem.id}/testcases')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('test_cases', json_response)
        self.assertEqual(len(json_response['test_cases']), 2)
        self.assertEqual(json.loads(json_response['test_cases'][0]['input_params']), {'param1': 'value1'})

    def test_get_all_test_cases_for_nonexistent_problem(self):
        response = self.client.get('/api/problems/999/testcases')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Problem not found', response.get_json()['message'])

    def test_get_specific_test_case_success(self):
        response = self.client.get(f'/api/testcases/{self.test_case1.id}')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['id'], self.test_case1.id)
        self.assertEqual(json.loads(json_response['input_params']), {'param1': 'value1'})

    def test_get_specific_test_case_not_found(self):
        response = self.client.get('/api/testcases/999') # Non-existent test case ID
        self.assertEqual(response.status_code, 404)

    def test_update_test_case_success(self):
        payload = {
            'input_params': json.dumps({'updated_param': 'updated_value'}),
            'expected_output': json.dumps('updated_expected')
        }
        response = self.client.put(f'/api/testcases/{self.test_case1.id}', json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json.loads(json_response['test_case']['input_params']), {'updated_param': 'updated_value'})

        updated_tc = TestCase.query.get(self.test_case1.id)
        self.assertEqual(json.loads(updated_tc.input_params), {'updated_param': 'updated_value'})

    def test_update_test_case_not_found(self):
        payload = {'input_params': json.dumps({})}
        response = self.client.put('/api/testcases/999', json=payload)
        self.assertEqual(response.status_code, 404)

    def test_delete_test_case_success(self):
        test_case_id_to_delete = self.test_case1.id
        response = self.client.delete(f'/api/testcases/{test_case_id_to_delete}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test case deleted successfully', response.get_json()['message'])

        deleted_tc = TestCase.query.get(test_case_id_to_delete)
        self.assertIsNone(deleted_tc)

    def test_delete_test_case_not_found(self):
        response = self.client.delete('/api/testcases/999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
