import unittest
import json
from app import create_app, db
from app.config import TestingConfig
from app.models import Candidate, Problem, TestCase, Submission, Setting, CandidateProblemTab
from unittest.mock import patch, MagicMock

class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # 创建测试数据
        # 1. 创建候选人
        self.candidate = Candidate(name="Test Candidate", email="test@example.com")
        self.candidate.set_password("testpassword")
        db.session.add(self.candidate)
        db.session.commit()

        # 2. 创建题目
        self.problem = Problem(
            title="Integration Test Problem",
            description="A problem for integration testing",
            llm_prompt="Review this code for integration testing."
        )
        db.session.add(self.problem)
        db.session.commit()

        # 3. 创建测试用例
        self.test_case = TestCase(
            problem_id=self.problem.id,
            input_params=json.dumps("test input"),
            expected_output=json.dumps("test output")
        )
        db.session.add(self.test_case)
        db.session.commit()

        # 4. 创建设置
        self.setting = Setting(key='deepseek_api_key', value='test_key')
        db.session.add(self.setting)
        db.session.commit()

        # 5. 配置 Judge0 API URL
        self.app.config['JUDGE0_API_URL'] = 'http://mockjudge0.com'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_complete_workflow(self):
        """测试完整的用户工作流程"""
        # 1. 为候选人添加题目 Tab
        response = self.client.post(
            f'/api/candidates/{self.candidate.id}/tabs',
            json={'problem_id': self.problem.id}
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(
            CandidateProblemTab.query.filter_by(
                candidate_id=self.candidate.id,
                problem_id=self.problem.id
            ).first()
        )

        # 2. 提交代码
        with patch('app.services.judge0_service.Judge0Service.submit_code') as mock_submit, \
             patch('app.services.judge0_service.Judge0Service.wait_for_submission') as mock_wait, \
             patch('app.api.submissions.generate_llm_review_async') as mock_llm:
            
            # 模拟 Judge0 服务响应
            mock_submit.return_value = 'test_token'
            mock_wait.return_value = {
                'status': {'id': 3, 'description': 'Accepted'},  # 3 表示成功
                'stdout': json.dumps('test output'),
                'stderr': None,
                'compile_output': None
            }
            mock_llm.return_value = None  # 异步 LLM 调用

            payload = {
                'candidate_id': self.candidate.id,
                'problem_id': self.problem.id,
                'language': 'python',
                'code': 'print("test output")'
            }
            response = self.client.post('/api/submissions', json=payload)
            self.assertEqual(response.status_code, 201)
            json_response = response.get_json()
            self.assertEqual(json_response['submission']['status'], 'Accepted')
            self.assertTrue(json_response['submission']['test_results'][0]['passed'])

        # 3. 获取提交历史
        response = self.client.get(f'/api/submissions/candidate/{self.candidate.id}/problem/{self.problem.id}')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(len(json_response['submissions']), 1)
        self.assertEqual(json_response['submissions'][0]['status'], 'Accepted')

        # 4. 更新设置
        response = self.client.put(
            '/api/settings/deepseek_api_key',
            json={'value': 'new_test_key'}
        )
        self.assertEqual(response.status_code, 200)
        updated_setting = Setting.query.get('deepseek_api_key')
        self.assertEqual(updated_setting.value, 'new_test_key')

        # 5. 移除 Tab
        response = self.client.delete(f'/api/candidates/{self.candidate.id}/tabs/{self.problem.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(
            CandidateProblemTab.query.filter_by(
                candidate_id=self.candidate.id,
                problem_id=self.problem.id
            ).first()
        )

    def test_error_handling(self):
        """测试错误处理流程"""
        # 1. 尝试为不存在的候选人添加 Tab
        response = self.client.post(
            '/api/candidates/999/tabs',
            json={'problem_id': self.problem.id}
        )
        self.assertEqual(response.status_code, 404)

        # 2. 尝试提交不存在的候选人的代码
        payload = {
            'candidate_id': 999,
            'problem_id': self.problem.id,
            'language': 'python',
            'code': 'print("test")'
        }
        response = self.client.post('/api/submissions', json=payload)
        self.assertEqual(response.status_code, 404)

        # 3. 尝试获取不存在的设置
        response = self.client.get('/api/settings/nonexistent_key')
        self.assertEqual(response.status_code, 404)

    def test_concurrent_operations(self):
        """测试并发操作"""
        # 1. 创建多个题目
        problem2 = Problem(
            title="Second Problem",
            description="Another problem",
            llm_prompt="Review this code."
        )
        problem3 = Problem(
            title="Third Problem",
            description="Yet another problem",
            llm_prompt="Review this code."
        )
        db.session.add_all([problem2, problem3])
        db.session.commit()

        # 为 problem2 和 problem3 添加测试用例
        test_case2 = TestCase(
            problem_id=problem2.id,
            input_params=json.dumps("test input"),
            expected_output=json.dumps("test output")
        )
        test_case3 = TestCase(
            problem_id=problem3.id,
            input_params=json.dumps("test input"),
            expected_output=json.dumps("test output")
        )
        db.session.add_all([test_case2, test_case3])
        db.session.commit()

        # 2. 为候选人添加多个 Tab
        for problem in [self.problem, problem2, problem3]:
            response = self.client.post(
                f'/api/candidates/{self.candidate.id}/tabs',
                json={'problem_id': problem.id}
            )
            self.assertEqual(response.status_code, 201)

        # 3. 验证所有 Tab 都已添加
        response = self.client.get(f'/api/candidates/{self.candidate.id}/tabs')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(len(json_response['tabs']), 3)

        # 4. 为每个题目提交代码
        with patch('app.services.judge0_service.Judge0Service.submit_code') as mock_submit, \
             patch('app.services.judge0_service.Judge0Service.wait_for_submission') as mock_wait, \
             patch('app.api.submissions.generate_llm_review_async') as mock_llm:
            
            mock_submit.return_value = 'test_token'
            mock_wait.return_value = {
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': json.dumps('test output'),
                'stderr': None,
                'compile_output': None
            }
            mock_llm.return_value = None

            for problem in [self.problem, problem2, problem3]:
                payload = {
                    'candidate_id': self.candidate.id,
                    'problem_id': problem.id,
                    'language': 'python',
                    'code': 'print("test output")'
                }
                response = self.client.post('/api/submissions', json=payload)
                self.assertEqual(response.status_code, 201)

        # 5. 验证所有提交都已记录
        for problem in [self.problem, problem2, problem3]:
            response = self.client.get(f'/api/submissions/candidate/{self.candidate.id}/problem/{problem.id}')
            self.assertEqual(response.status_code, 200)
            json_response = response.get_json()
            self.assertEqual(len(json_response['submissions']), 1)
            self.assertEqual(json_response['submissions'][0]['status'], 'Accepted')

if __name__ == '__main__':
    unittest.main() 
