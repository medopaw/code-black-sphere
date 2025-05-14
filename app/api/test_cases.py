from flask import Blueprint, request, jsonify
from app import db
from app.models import Problem, TestCase

test_cases_bp = Blueprint('test_cases_bp', __name__, url_prefix='/api')

@test_cases_bp.route('/problems/<int:problem_id>/testcases', methods=['POST'])
def create_test_case(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        return jsonify({'message': 'Problem not found'}), 404
    
    data = request.get_json()
    if not data or 'input_params' not in data or 'expected_output' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
    
    new_test_case = TestCase(
        problem_id=problem_id,
        input_params=data['input_params'],
        expected_output=data['expected_output']
    )
    db.session.add(new_test_case)
    db.session.commit()
    
    return jsonify({
        'test_case': {
            'id': new_test_case.id,
            'problem_id': new_test_case.problem_id,
            'input_params': new_test_case.input_params,
            'expected_output': new_test_case.expected_output
        }
    }), 201

@test_cases_bp.route('/problems/<int:problem_id>/testcases', methods=['GET'])
def get_test_cases(problem_id):
    problem = Problem.query.get(problem_id)
    if not problem:
        return jsonify({'message': 'Problem not found'}), 404
    
    test_cases = TestCase.query.filter_by(problem_id=problem_id).all()
    return jsonify({
        'test_cases': [{
            'id': tc.id,
            'problem_id': tc.problem_id,
            'input_params': tc.input_params,
            'expected_output': tc.expected_output
        } for tc in test_cases]
    })

@test_cases_bp.route('/testcases/<int:test_case_id>', methods=['GET'])
def get_test_case(test_case_id):
    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        return jsonify({'message': 'Test case not found'}), 404
    
    return jsonify({
        'id': test_case.id,
        'problem_id': test_case.problem_id,
        'input_params': test_case.input_params,
        'expected_output': test_case.expected_output
    })

@test_cases_bp.route('/testcases/<int:test_case_id>', methods=['PUT'])
def update_test_case(test_case_id):
    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        return jsonify({'message': 'Test case not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    if 'input_params' in data:
        test_case.input_params = data['input_params']
    if 'expected_output' in data:
        test_case.expected_output = data['expected_output']
    
    db.session.commit()
    
    return jsonify({
        'test_case': {
            'id': test_case.id,
            'problem_id': test_case.problem_id,
            'input_params': test_case.input_params,
            'expected_output': test_case.expected_output
        }
    })

@test_cases_bp.route('/testcases/<int:test_case_id>', methods=['DELETE'])
def delete_test_case(test_case_id):
    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        return jsonify({'message': 'Test case not found'}), 404
    
    db.session.delete(test_case)
    db.session.commit()
    
    return jsonify({'message': 'Test case deleted successfully'})
