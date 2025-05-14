import unittest
import json
from app import create_app, db
from app.config import TestingConfig
from app.models import Candidate

class CandidatesAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Initial candidate for GET, PUT, DELETE tests
        self.candidate1 = Candidate(name="Initial Candidate", email="initial@example.com")
        self.candidate1.set_password("initialpass")
        db.session.add(self.candidate1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_candidate_success(self):
        payload = {
            'name': 'New Candidate',
            'email': 'new@example.com',
            'password': 'newpassword'
        }
        response = self.client.post('/api/candidates', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertIn('candidate', json_response)
        self.assertEqual(json_response['candidate']['name'], 'New Candidate')
        self.assertEqual(json_response['candidate']['email'], 'new@example.com')
        
        # Verify candidate is in DB
        candidate = Candidate.query.filter_by(email='new@example.com').first()
        self.assertIsNotNone(candidate)
        self.assertTrue(candidate.check_password('newpassword'))

    def test_create_candidate_missing_fields(self):
        payload = {'name': 'Missing Email'}
        response = self.client.post('/api/candidates', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing name or email', response.get_json()['message'])

    def test_create_candidate_duplicate_email(self):
        payload = {
            'name': 'Duplicate Email Candidate',
            'email': 'initial@example.com', # Existing email
            'password': 'password123'
        }
        response = self.client.post('/api/candidates', json=payload)
        self.assertEqual(response.status_code, 409) # Changed from 400 to 409
        self.assertIn('Candidate with this email already exists', response.get_json()['message'])
        
    def test_create_candidate_duplicate_name(self):
        payload = {
            'name': 'Initial Candidate', # Existing name
            'email': 'unique_email@example.com',
            'password': 'password123'
        }
        response = self.client.post('/api/candidates', json=payload)
        self.assertEqual(response.status_code, 409) # Changed from 400 to 409
        self.assertIn('Candidate name already exists', response.get_json()['message'])

    def test_get_all_candidates(self):
        # Add another candidate for list testing
        candidate2 = Candidate(name="Second Candidate", email="second@example.com")
        candidate2.set_password("secondpass")
        db.session.add(candidate2)
        db.session.commit()

        response = self.client.get('/api/candidates')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        # self.assertIn('candidates', json_response) # The API returns a list directly
        self.assertEqual(len(json_response), 2)
        self.assertEqual(json_response[0]['name'], 'Initial Candidate')
        self.assertEqual(json_response[1]['name'], 'Second Candidate')

    def test_get_specific_candidate_success(self):
        response = self.client.get(f'/api/candidates/{self.candidate1.id}')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['name'], self.candidate1.name)
        self.assertEqual(json_response['email'], self.candidate1.email)

    def test_get_specific_candidate_not_found(self):
        response = self.client.get('/api/candidates/999') # Non-existent ID
        self.assertEqual(response.status_code, 404)
        # For 404, a JSON body with 'message' is not guaranteed, so we only check status code.

    def test_update_candidate_success(self):
        payload = {
            'name': 'Updated Name',
            'email': 'updated@example.com'
            # Password update can be a separate test or endpoint if needed
        }
        response = self.client.put(f'/api/candidates/{self.candidate1.id}', json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['candidate']['name'], 'Updated Name')
        self.assertEqual(json_response['candidate']['email'], 'updated@example.com')

        # Verify in DB
        updated_candidate = Candidate.query.get(self.candidate1.id)
        self.assertEqual(updated_candidate.name, 'Updated Name')
        self.assertEqual(updated_candidate.email, 'updated@example.com')

    def test_update_candidate_not_found(self):
        payload = {'name': 'No Such Candidate'}
        response = self.client.put('/api/candidates/999', json=payload)
        self.assertEqual(response.status_code, 404)

    def test_update_candidate_duplicate_email_on_update(self):
        # Create another candidate
        candidate2 = Candidate(name="Other Candidate", email="other@example.com")
        db.session.add(candidate2)
        db.session.commit()

        payload = {'email': 'other@example.com'} # Try to update candidate1's email to candidate2's email
        response = self.client.put(f'/api/candidates/{self.candidate1.id}', json=payload)
        self.assertEqual(response.status_code, 409) # Changed from 400 to 409
        self.assertIn('Email already in use by another candidate', response.get_json()['message'])

    def test_delete_candidate_success(self):
        response = self.client.delete(f'/api/candidates/{self.candidate1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Candidate deleted successfully', response.get_json()['message'])

        # Verify not in DB
        deleted_candidate = Candidate.query.get(self.candidate1.id)
        self.assertIsNone(deleted_candidate)

    def test_delete_candidate_not_found(self):
        response = self.client.delete('/api/candidates/999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
