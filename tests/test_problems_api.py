import unittest
import json
from app import create_app, db
from app.config import TestingConfig as Config
import io
from app.models import Problem, TestCase

class ProblemsAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=Config) # Will now use TestingConfig as Config
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Initial problem for GET, PUT, DELETE tests
        self.problem1 = Problem(title="Initial Problem", description="Desc 1", llm_prompt="Prompt 1")
        db.session.add(self.problem1)
        db.session.commit()

        self.test_case1_p1 = TestCase(problem_id=self.problem1.id, input_params=json.dumps([1,2]), expected_output=json.dumps(3))
        db.session.add(self.test_case1_p1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_problem_success(self):
        payload = {
            'title': 'New Problem',
            'description': 'A new test problem.',
            'llm_prompt': 'Review this new code.'
        }
        response = self.client.post('/api/problems', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertIn('problem', json_response)
        self.assertEqual(json_response['problem']['title'], 'New Problem')
        self.assertEqual(json_response['problem']['description'], 'A new test problem.')
        
        problem = Problem.query.filter_by(title='New Problem').first()
        self.assertIsNotNone(problem)

    def test_create_problem_missing_title(self):
        payload = {'description': 'Missing title problem.'}
        response = self.client.post('/api/problems', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing required fields', response.get_json()['message'])

    def test_create_problem_duplicate_title(self):
        payload = {'title': 'Initial Problem', 'description': 'Duplicate title.', 'llm_prompt': 'Some prompt for duplicate.'}
        response = self.client.post('/api/problems', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Problem title already exists', response.get_json()['message'])

    def test_get_all_problems(self):
        problem2 = Problem(title="Second Problem", description="Desc 2")
        db.session.add(problem2)
        db.session.commit()

        response = self.client.get('/api/problems')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('problems', json_response)
        self.assertEqual(len(json_response['problems']), 2)
        self.assertEqual(json_response['problems'][0]['title'], 'Initial Problem')
        self.assertEqual(json_response['problems'][1]['title'], 'Second Problem')

    def test_get_specific_problem_success(self):
        response = self.client.get(f'/api/problems/{self.problem1.id}')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['title'], self.problem1.title)
        self.assertEqual(json_response['description'], self.problem1.description)
        self.assertIn('test_cases', json_response)
        self.assertEqual(len(json_response['test_cases']), 1)
        self.assertEqual(json.loads(json_response['test_cases'][0]['input_params']), [1,2])

    def test_get_specific_problem_not_found(self):
        response = self.client.get('/api/problems/999')
        self.assertEqual(response.status_code, 404)

    def test_update_problem_success(self):
        payload = {
            'title': 'Updated Problem Title',
            'description': 'Updated description.',
            'llm_prompt': 'Updated prompt.'
        }
        response = self.client.put(f'/api/problems/{self.problem1.id}', json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['problem']['title'], 'Updated Problem Title')
        
        updated_problem = Problem.query.get(self.problem1.id)
        self.assertEqual(updated_problem.title, 'Updated Problem Title')
        self.assertEqual(updated_problem.description, 'Updated description.')

    def test_update_problem_not_found(self):
        payload = {'title': 'No Such Problem'}
        response = self.client.put('/api/problems/999', json=payload)
        self.assertEqual(response.status_code, 404)

    def test_update_problem_duplicate_title_on_update(self):
        problem2 = Problem(title="Unique Problem 2", description="Desc Unique")
        db.session.add(problem2)
        db.session.commit()

        payload = {'title': 'Unique Problem 2'} # Try to update problem1's title to problem2's title
        response = self.client.put(f'/api/problems/{self.problem1.id}', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Problem title already exists', response.get_json()['message'])

    def test_delete_problem_success(self):
        problem_to_delete_id = self.problem1.id
        # Ensure test cases associated are also deleted due to cascade
        self.assertIsNotNone(TestCase.query.filter_by(problem_id=problem_to_delete_id).first())

        response = self.client.delete(f'/api/problems/{problem_to_delete_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Problem deleted successfully', response.get_json()['message'])

        deleted_problem = Problem.query.get(problem_to_delete_id)
        self.assertIsNone(deleted_problem)
        # Verify cascade delete for test cases
        self.assertIsNone(TestCase.query.filter_by(problem_id=problem_to_delete_id).first())

    def test_delete_problem_not_found(self):
        response = self.client.delete('/api/problems/999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':

    def test_import_problems_success(self):
        # Create a sample JSON file content for import
        problems_data = [
            {"title": "Imported Problem 1", "description": "Desc Import 1", "llm_prompt": "Prompt Import 1"},
            {"title": "Imported Problem 2", "description": "Desc Import 2", "llm_prompt": "Prompt Import 2"}
        ]
        file_content = json.dumps(problems_data)
        data = {'file': (io.BytesIO(file_content.encode('utf-8')), 'test_problems.json')}

        response = self.client.post('/api/problems/import', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertIn('message', json_response)
        self.assertEqual(json_response['message'], 'Problems imported successfully')
        self.assertEqual(json_response['imported_count'], 2)
        self.assertEqual(json_response['skipped_count'], 0)

        # Verify in DB
        p1 = Problem.query.filter_by(title="Imported Problem 1").first()
        self.assertIsNotNone(p1)
        self.assertEqual(p1.description, "Desc Import 1")
        p2 = Problem.query.filter_by(title="Imported Problem 2").first()
        self.assertIsNotNone(p2)

    def test_import_problems_empty_file(self):
        file_content = json.dumps([])
        data = {'file': (io.BytesIO(file_content.encode('utf-8')), 'empty.json')}
        response = self.client.post('/api/problems/import', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('No problems found in the file', response.get_json()['message'])

    def test_import_problems_invalid_file_format(self):
        # Not a JSON file
        file_content = "This is not a json file"
        data = {'file': (io.BytesIO(file_content.encode('utf-8')), 'invalid.txt')}
        response = self.client.post('/api/problems/import', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid file format or content', response.get_json()['message'])

    def test_import_problems_missing_file(self):
        response = self.client.post('/api/problems/import', content_type='multipart/form-data', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('No file part', response.get_json()['message'])

    def test_import_problems_duplicate_title_in_file_and_db(self):
        # self.problem1 (title="Initial Problem") already exists
        problems_data = [
            {"title": "Initial Problem", "description": "Desc Import Duplicate", "llm_prompt": "Prompt Import Duplicate"},
            {"title": "Imported Problem Unique", "description": "Desc Import Unique", "llm_prompt": "Prompt Import Unique"}
        ]
        file_content = json.dumps(problems_data)
        data = {'file': (io.BytesIO(file_content.encode('utf-8')), 'test_problems_duplicates.json')}

        response = self.client.post('/api/problems/import', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 201) # Partial success
        json_response = response.get_json()
        self.assertEqual(json_response['imported_count'], 1)
        self.assertEqual(json_response['skipped_count'], 1)
        self.assertIn('Problem with title \'Initial Problem\' already exists and was skipped.', json_response['details'])

        # Verify only unique one was added
        p_dup = Problem.query.filter_by(title="Initial Problem").first()
        self.assertEqual(p_dup.description, "Desc 1") # Original description, not updated
        p_unique = Problem.query.filter_by(title="Imported Problem Unique").first()
        self.assertIsNotNone(p_unique)

    def test_import_problems_missing_required_fields_in_file(self):
        problems_data = [
            {"description": "Missing title here"} # Missing title
        ]
        file_content = json.dumps(problems_data)
        data = {'file': (io.BytesIO(file_content.encode('utf-8')), 'test_problems_missing_fields.json')}

        response = self.client.post('/api/problems/import', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 201) # Partial success or specific error handling
        json_response = response.get_json()
        self.assertEqual(json_response['imported_count'], 0)
        self.assertEqual(json_response['skipped_count'], 1)
        self.assertIn('Missing required fields (title) for a problem in the file.', json_response['details'])

    def test_export_problems_success(self):
        # Add another problem to export
        problem2 = Problem(title="Export Problem 2", description="Desc Export 2", llm_prompt="Prompt Export 2")
        db.session.add(problem2)
        db.session.commit()

        response = self.client.get('/api/problems/export')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn('attachment; filename=problems_export.json', response.headers['Content-Disposition'])

        exported_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(exported_data), 2)
        titles = [p['title'] for p in exported_data]
        self.assertIn('Initial Problem', titles)
        self.assertIn('Export Problem 2', titles)
        # Check for specific fields (assuming default export includes these)
        for p_data in exported_data:
            self.assertIn('title', p_data)
            self.assertIn('description', p_data)
            self.assertIn('llm_prompt', p_data)
            self.assertNotIn('id', p_data) # IDs should not be exported for re-import
            self.assertNotIn('created_at', p_data)
            self.assertNotIn('updated_at', p_data)

    def test_export_problems_no_problems_to_export(self):
        # Delete existing problems
        Problem.query.delete()
        db.session.commit()

        response = self.client.get('/api/problems/export')
        self.assertEqual(response.status_code, 200) # Or 204 No Content, depending on API design
        exported_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(exported_data), 0)

if __name__ == '__main__':
    unittest.main()
