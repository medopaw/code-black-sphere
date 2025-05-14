import unittest
import json
from app import create_app, db
from app.config import TestingConfig as Config
from app.models import Setting

class SettingsAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=Config) # Will now use TestingConfig as Config
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Initial settings
        self.setting1 = Setting(key='deepseek_api_key', value='testkey123')
        self.setting2 = Setting(key='default_problem_id', value='10')
        db.session.add_all([self.setting1, self.setting2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_all_settings(self):
        response = self.client.get('/api/settings')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('settings', json_response)
        self.assertEqual(len(json_response['settings']), 2)
        settings_dict = {s['key']: s['value'] for s in json_response['settings']}
        self.assertEqual(settings_dict['deepseek_api_key'], 'testkey123')
        self.assertEqual(settings_dict['default_problem_id'], '10')

    def test_get_specific_setting_success(self):
        response = self.client.get(f'/api/settings/{self.setting1.key}')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['key'], self.setting1.key)
        self.assertEqual(json_response['value'], self.setting1.value)

    def test_get_specific_setting_not_found(self):
        response = self.client.get('/api/settings/nonexistent_key')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Setting not found', response.get_json()['message'])

    def test_update_existing_setting_success(self):
        payload = {'value': 'newapikey456'}
        response = self.client.put(f'/api/settings/{self.setting1.key}', json=payload)
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['setting']['key'], self.setting1.key)
        self.assertEqual(json_response['setting']['value'], 'newapikey456')

        updated_setting = Setting.query.get(self.setting1.key)
        self.assertEqual(updated_setting.value, 'newapikey456')

    def test_create_new_setting_via_put_success(self):
        new_key = 'new_feature_flag'
        payload = {'value': 'true'}
        response = self.client.put(f'/api/settings/{new_key}', json=payload)
        self.assertEqual(response.status_code, 201) # 201 for created
        json_response = response.get_json()
        self.assertEqual(json_response['setting']['key'], new_key)
        self.assertEqual(json_response['setting']['value'], 'true')

        created_setting = Setting.query.get(new_key)
        self.assertIsNotNone(created_setting)
        self.assertEqual(created_setting.value, 'true')

    def test_update_setting_missing_value(self):
        payload = {} # Missing 'value'
        response = self.client.put(f'/api/settings/{self.setting1.key}', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing value field', response.get_json()['message'])
    
    def test_update_setting_empty_key(self):
        payload = {'value': 'some_value'}
        response = self.client.put('/api/settings/%20%20', json=payload) # Empty or whitespace key
        self.assertEqual(response.status_code, 400)
        self.assertIn('Setting key cannot be empty', response.get_json()['message'])

if __name__ == '__main__':
    unittest.main()
