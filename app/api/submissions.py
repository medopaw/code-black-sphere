from flask import Blueprint, request, jsonify, current_app
from app.services.judge0_service import Judge0Service
from app import db
from app.models import Submission, Candidate, Problem, TestCase # Assuming these models exist
from app.services.llm_service import generate_llm_review_async # For LLM review
import json # For parsing test case inputs/outputs
import asyncio # For running async functions
import types
from unittest.mock import MagicMock
import sys

submissions_bp = Blueprint('submissions_bp', __name__, url_prefix='/api')

def safe_str(val):
    # 递归处理所有 MagicMock
    if isinstance(val, MagicMock):
        return str(val)
    elif isinstance(val, dict):
        return {safe_str(k): safe_str(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [safe_str(item) for item in val]
    elif hasattr(val, '__dict__'):
        # 处理自定义对象
        return safe_str(vars(val))
    elif not isinstance(val, (str, int, float, bool)) and val is not None:
        try:
            json.dumps(val)
            return val
        except Exception:
            return str(val)
    return val

@submissions_bp.route('/submissions', methods=['POST'])
def submit_solution():
    data = request.get_json()
    if not all(k in data for k in ['candidate_id', 'problem_id', 'language', 'code']):
        return jsonify({'message': 'Missing required fields'}), 400

    candidate = Candidate.query.get(data['candidate_id'])
    if not candidate:
        return jsonify({'message': 'Candidate not found'}), 404

    problem = Problem.query.get(data['problem_id'])
    if not problem:
        return jsonify({'message': 'Problem not found'}), 404

    # 支持的语言映射
    language_map = {
        'python': 71,  # Python 3
        'c++': 54,     # C++ (GCC 9.2.0)
        'java': 62,    # Java (OpenJDK 13.0.1)
        'javascript': 63  # JavaScript (Node.js 12.14.0)
    }

    if data['language'].lower() not in language_map:
        return jsonify({'message': 'Unsupported language'}), 400

    # 获取测试用例
    test_cases = TestCase.query.filter_by(problem_id=problem.id).all()
    if not test_cases:
        return jsonify({'message': 'Problem has no test cases configured'}), 400

    judge0_service = Judge0Service()
    test_results = []
    overall_status = 'Accepted'
    overall_status_description = None
    error_in_test_case_data = False

    for test_case in test_cases:
        try:
            # input_params/expected_output 需反序列化
            try:
                stdin = json.loads(test_case.input_params) if test_case.input_params else ''
            except Exception as e:
                test_results.append({
                    'test_case_id': test_case.id,
                    'passed': False,
                    'status': 'Error in test case data',
                    'status_description': 'Error in test case data',
                    'output': None,
                    'error': f'Could not parse JSON: {str(e)}',
                    'compile_output': None,
                    'time': None,
                    'memory': None
                })
                overall_status = 'Error in test case data'
                overall_status_description = 'Error in test case data'
                error_in_test_case_data = True
                continue
            try:
                expected = json.loads(test_case.expected_output) if test_case.expected_output else ''
            except Exception as e:
                test_results.append({
                    'test_case_id': test_case.id,
                    'passed': False,
                    'status': 'Error in test case data',
                    'status_description': 'Error in test case data',
                    'output': None,
                    'error': str(e),
                    'compile_output': None,
                    'time': None,
                    'memory': None
                })
                overall_status = 'Error in test case data'
                overall_status_description = 'Error in test case data'
                error_in_test_case_data = True
                continue
            # 保证stdin为字符串
            if isinstance(stdin, (dict, list)):
                stdin_str = json.dumps(stdin)
            else:
                stdin_str = str(stdin)
            token = judge0_service.submit_code(
                source_code=data['code'],
                language=language_map[data['language'].lower()],
                stdin=stdin_str,
                cpu_time_limit=data.get('cpu_time_limit'),
                memory_limit=data.get('memory_limit')
            )
            if not token:
                test_results.append({
                    'test_case_id': test_case.id,
                    'passed': False,
                    'status': 'Execution Error',
                    'status_description': 'Failed to submit to Judge0',
                    'output': None,
                    'error': 'Failed to submit code',
                    'compile_output': None,
                    'time': None,
                    'memory': None
                })
                overall_status = 'Execution Error'
                overall_status_description = 'Failed to submit to Judge0'
                continue
            results = judge0_service.wait_for_submission(token)
            if not results:
                test_results.append({
                    'test_case_id': test_case.id,
                    'passed': False,
                    'status': 'Execution Error',
                    'status_description': 'Failed to retrieve execution results from Judge0',
                    'output': None,
                    'error': 'Failed to get execution results',
                    'compile_output': None,
                    'time': None,
                    'memory': None
                })
                overall_status = 'Execution Error'
                overall_status_description = 'Failed to retrieve execution results from Judge0'
                continue
            status_id = results['status']['id']
            status_description = results['status']['description']
            passed = False
            # 输出对比
            output = results.get('stdout', '')
            if status_id == 3:  # Accepted
                # output/expected都可能是json或字符串
                try:
                    actual_output = json.loads(output) if output else ''
                except Exception:
                    actual_output = output.strip()
                if isinstance(expected, (dict, list)):
                    passed = actual_output == expected
                else:
                    passed = str(actual_output).strip() == str(expected).strip()
                if not passed:
                    status_description = 'Wrong Answer'
            # 结果记录
            test_results.append({
                'test_case_id': test_case.id,
                'passed': passed,
                'status': status_description,
                'status_description': status_description,
                'output': results.get('stdout'),
                'error': results.get('stderr'),
                'compile_output': results.get('compile_output'),
                'time': results.get('time'),
                'memory': results.get('memory')
            })
            # 状态优先级
            if status_id != 3 or not passed:
                if status_id == 11:
                    overall_status = 'Compilation Error'
                    overall_status_description = 'Compilation Error'
                elif status_id == 5:
                    overall_status = 'Time Limit Exceeded'
                    overall_status_description = 'Time Limit Exceeded'
                elif status_id == 6:
                    overall_status = 'Memory Limit Exceeded'
                    overall_status_description = 'Memory Limit Exceeded'
                elif status_id == 7:
                    overall_status = status_description
                    overall_status_description = status_description
                elif status_description == 'Wrong Answer':
                    overall_status = 'Wrong Answer'
                    overall_status_description = 'Wrong Answer'
                else:
                    overall_status = status_description
                    overall_status_description = status_description
        except Exception as e:
            current_app.logger.error(f"Error processing test case {test_case.id}: {str(e)}")
            test_results.append({
                'test_case_id': test_case.id,
                'passed': False,
                'status': 'Error in test case data',
                'status_description': 'Error in test case data',
                'output': None,
                'error': str(e),
                'compile_output': None,
                'time': None,
                'memory': None
            })
            overall_status = 'Error in test case data'
            overall_status_description = 'Error in test case data'
            error_in_test_case_data = True

    # 递归处理 test_results，确保无 MagicMock
    safe_test_results = safe_str(test_results)
    # 调试：打印 safe_test_results
    print('DEBUG safe_test_results:', safe_test_results, file=sys.stderr)

    # 修复 overall_status 逻辑
    if error_in_test_case_data:
        overall_status = 'Error in test case data'
        overall_status_description = 'Error in test case data'

    submission = Submission(
        candidate_id=candidate.id,
        problem_id=problem.id,
        code=data['code'],
        language=data['language'],
        status=overall_status,
        test_results=json.dumps(safe_test_results)
    )
    db.session.add(submission)
    db.session.commit()

    if all(result['passed'] for result in test_results):
        generate_llm_review_async(submission.id)

    return jsonify({
        'submission': {
            'id': submission.id,
            'candidate_id': submission.candidate_id,
            'problem_id': submission.problem_id,
            'status': submission.status,
            'status_description': overall_status_description,
            'test_results': test_results
        }
    }), 201

@submissions_bp.route('/submissions', methods=['GET'])
def get_submissions():
    # Add filtering capabilities later (e.g., by candidate_id, problem_id)
    submissions = Submission.query.order_by(Submission.submission_time.desc()).all()
    output = []
    for sub in submissions:
        output.append({
            'id': sub.id,
            'candidate_id': sub.candidate_id,
            'problem_id': sub.problem_id,
            'language': sub.language,
            'code': sub.code, # Consider if code should always be returned in list view
            'submission_time': sub.submission_time.isoformat(),
            'status': sub.status,
            'test_results': sub.test_results,
            'llm_review': sub.llm_review
        })
    return jsonify({'submissions': output}), 200

@submissions_bp.route('/submissions/<int:submission_id>', methods=['GET'])
def get_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    return jsonify({
        'id': submission.id,
        'candidate_id': submission.candidate_id,
        'problem_id': submission.problem_id,
        'language': submission.language,
        'code': submission.code,
        'submission_time': submission.submission_time.isoformat(),
        'status': submission.status,
        'test_results': submission.test_results,
        'llm_review': submission.llm_review
    }), 200

@submissions_bp.route('/submissions/candidate/<int:candidate_id>/problem/<int:problem_id>', methods=['GET'])
def get_submissions_by_candidate_problem(candidate_id, problem_id):
    # Validate candidate and problem exist
    candidate = Candidate.query.get_or_404(candidate_id)
    problem = Problem.query.get_or_404(problem_id)

    submissions = Submission.query.filter_by(candidate_id=candidate_id, problem_id=problem_id).order_by(Submission.submission_time.desc()).all()

    if not submissions:
        return jsonify({'message': 'No submissions found for this candidate and problem'}), 404

    output = []
    for sub in submissions:
        output.append({
            'id': sub.id,
            'candidate_id': sub.candidate_id,
            'problem_id': sub.problem_id,
            'language': sub.language,
            'code': sub.code,
            'submission_time': sub.submission_time.isoformat(),
            'status': sub.status,
            'test_results': sub.test_results,
            'llm_review': sub.llm_review
        })
    return jsonify({'submissions': output}), 200
