import unittest
import json
from app import create_app, db
from app.models import Candidate, Problem, CandidateProblemTab
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TabsAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a candidate
        self.candidate = Candidate(name="Tab Candidate", email="tab_candidate@example.com")
        self.candidate.set_password("password")
        db.session.add(self.candidate)
        db.session.commit()

        # Create problems
        self.problem1 = Problem(title="Tab Problem 1", description="Problem 1 for tabs")
        self.problem2 = Problem(title="Tab Problem 2", description="Problem 2 for tabs")
        self.problem3 = Problem(title="Tab Problem 3", description="Problem 3 for tabs")
        db.session.add_all([self.problem1, self.problem2, self.problem3])
        db.session.commit()

        # Pre-existing tab for the candidate
        self.tab1 = CandidateProblemTab(candidate_id=self.candidate.id, problem_id=self.problem1.id, tab_order=1)
        db.session.add(self.tab1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_new_tab_success(self):
        payload = {'problem_id': self.problem2.id}
        response = self.client.post(f'/api/candidates/{self.candidate.id}/tabs', json=payload)
        self.assertEqual(response.status_code, 201)
        json_response = response.get_json()
        self.assertIn('tab', json_response)
        self.assertEqual(json_response['tab']['problem_id'], self.problem2.id)
        self.assertEqual(json_response['tab']['candidate_id'], self.candidate.id)
        # Check tab_order logic if implemented, otherwise just check existence
        self.assertIsNotNone(CandidateProblemTab.query.filter_by(candidate_id=self.candidate.id, problem_id=self.problem2.id).first())

    def test_add_existing_tab_fails(self):
        payload = {'problem_id': self.problem1.id} # Already a tab
        response = self.client.post(f'/api/candidates/{self.candidate.id}/tabs', json=payload)
        self.assertEqual(response.status_code, 400) # Or 409 Conflict
        self.assertIn('Tab for this problem already exists', response.get_json()['message'])

    def test_add_tab_for_nonexistent_candidate(self):
        payload = {'problem_id': self.problem1.id}
        response = self.client.post('/api/candidates/999/tabs', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Candidate not found', response.get_json()['message'])

    def test_add_tab_for_nonexistent_problem(self):
        payload = {'problem_id': 999}
        response = self.client.post(f'/api/candidates/{self.candidate.id}/tabs', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Problem not found', response.get_json()['message'])

    def test_get_candidate_tabs_success(self):
        # Add another tab for listing
        tab2 = CandidateProblemTab(candidate_id=self.candidate.id, problem_id=self.problem2.id, tab_order=2)
        db.session.add(tab2)
        db.session.commit()

        response = self.client.get(f'/api/candidates/{self.candidate.id}/tabs')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('tabs', json_response)
        self.assertEqual(len(json_response['tabs']), 2)
        # Assuming tabs are ordered by tab_order
        self.assertEqual(json_response['tabs'][0]['problem_id'], self.problem1.id)
        self.assertEqual(json_response['tabs'][1]['problem_id'], self.problem2.id)

    def test_get_tabs_for_nonexistent_candidate(self):
        response = self.client.get('/api/candidates/999/tabs')
        self.assertEqual(response.status_code, 404)

    def test_remove_tab_success(self):
        response = self.client.delete(f'/api/candidates/{self.candidate.id}/tabs/{self.problem1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tab removed successfully', response.get_json()['message'])
        self.assertIsNone(CandidateProblemTab.query.filter_by(candidate_id=self.candidate.id, problem_id=self.problem1.id).first())

    def test_remove_nonexistent_tab(self):
        response = self.client.delete(f'/api/candidates/{self.candidate.id}/tabs/{self.problem3.id}') # problem3 is not a tab yet
        self.assertEqual(response.status_code, 404)
        self.assertIn('Tab not found', response.get_json()['message'])

    def test_remove_tab_for_nonexistent_candidate(self):
        response = self.client.delete(f'/api/candidates/999/tabs/{self.problem1.id}')
        self.assertEqual(response.status_code, 404)

    def test_update_tab_order_success(self):
        # Add more tabs for reordering
        tab2 = CandidateProblemTab(candidate_id=self.candidate.id, problem_id=self.problem2.id, tab_order=2)
        tab3 = CandidateProblemTab(candidate_id=self.candidate.id, problem_id=self.problem3.id, tab_order=3)
        db.session.add_all([tab2, tab3])
        db.session.commit()

        # New order: problem2, problem3, problem1
        payload = {'ordered_problem_ids': [self.problem2.id, self.problem3.id, self.problem1.id]}
        response = self.client.put(f'/api/candidates/{self.candidate.id}/tabs', json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('tabs', json_response)
        self.assertEqual(len(json_response['tabs']), 3)
        self.assertEqual(json_response['tabs'][0]['problem_id'], self.problem2.id)
        self.assertEqual(json_response['tabs'][0]['tab_order'], 1)
        self.assertEqual(json_response['tabs'][1]['problem_id'], self.problem3.id)
        self.assertEqual(json_response['tabs'][1]['tab_order'], 2)
        self.assertEqual(json_response['tabs'][2]['problem_id'], self.problem1.id)
        self.assertEqual(json_response['tabs'][2]['tab_order'], 3)

    def test_update_tab_order_nonexistent_candidate(self):
        payload = {'ordered_problem_ids': [self.problem1.id]}
        response = self.client.put('/api/candidates/999/tabs', json=payload)
        self.assertEqual(response.status_code, 404)

    def test_update_tab_order_problem_not_in_candidates_tabs(self):
        # problem3 is not initially a tab for self.candidate (only problem1 is)
        payload = {'ordered_problem_ids': [self.problem3.id, self.problem1.id]}
        response = self.client.put(f'/api/candidates/{self.candidate.id}/tabs', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('contains problem IDs not currently in the candidate tabs', response.get_json()['message'])

    def test_update_tab_order_missing_problem_from_candidates_tabs(self):
        tab2 = CandidateProblemTab(candidate_id=self.candidate.id, problem_id=self.problem2.id, tab_order=2)
        db.session.add(tab2)
        db.session.commit()
        # Candidate has tabs for problem1 and problem2, but payload only sends problem1
        payload = {'ordered_problem_ids': [self.problem1.id]}
        response = self.client.put(f'/api/candidates/{self.candidate.id}/tabs', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('does not match the set of current tabs', response.get_json()['message'])

if __name__ == '__main__':
    unittest.main()
