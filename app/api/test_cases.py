from flask import Blueprint, request, jsonify
from app import db
from app.models import Problem, TestCase

test_cases_bp = Blueprint('test_cases_bp', __name__, url_prefix='/api')

@test_cases_bp.route('/problems/<int:problem_id>/testcases', methods=['POST'])
def create_test_case(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    data = request.get_json()
    if not data or not 'input' in data or not 'expected_output' in data:
        return jsonify({'message': 'Missing input or expected_output'}), 400

    new_test_case = TestCase(
        problem_id=problem.id,
        input=data['input'],
        expected_output=data['expected_output'],
        is_public=data.get('is_public', True)  # Default to public if not specified
    )
    db.session.add(new_test_case)
    db.session.commit()

    return jsonify({'message': 'Test case created successfully', 'test_case': {'id': new_test_case.id, 'problem_id': new_test_case.problem_id, 'input': new_test_case.input, 'expected_output': new_test_case.expected_output, 'is_public': new_test_case.is_public}}), 201

@test_cases_bp.route('/problems/<int:problem_id>/testcases', methods=['GET'])
def get_test_cases_for_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    test_cases = TestCase.query.filter_by(problem_id=problem.id).all()
    if not test_cases:
        return jsonify({'message': 'No test cases found for this problem'}), 404

    output = []
    for tc in test_cases:
        output.append({
            'id': tc.id,
            'problem_id': tc.problem_id,
            'input': tc.input,
            'expected_output': tc.expected_output,
            'is_public': tc.is_public
        })
    return jsonify({'test_cases': output}), 200

@test_cases_bp.route('/testcases/<int:test_case_id>', methods=['GET'])
def get_test_case(test_case_id):
    test_case = TestCase.query.get_or_404(test_case_id)
    return jsonify({
        'id': test_case.id,
        'problem_id': test_case.problem_id,
        'input': test_case.input,
        'expected_output': test_case.expected_output,
        'is_public': test_case.is_public
    }), 200

@test_cases_bp.route('/testcases/<int:test_case_id>', methods=['PUT'])
def update_test_case(test_case_id):
    test_case = TestCase.query.get_or_404(test_case_id)
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    test_case.input = data.get('input', test_case.input)
    test_case.expected_output = data.get('expected_output', test_case.expected_output)
    test_case.is_public = data.get('is_public', test_case.is_public)

    db.session.commit()
    return jsonify({'message': 'Test case updated successfully', 'test_case': {'id': test_case.id, 'problem_id': test_case.problem_id, 'input': test_case.input, 'expected_output': test_case.expected_output, 'is_public': test_case.is_public}}), 200

@test_cases_bp.route('/testcases/<int:test_case_id>', methods=['DELETE'])
def delete_test_case(test_case_id):
    test_case = TestCase.query.get_or_404(test_case_id)
    db.session.delete(test_case)
    db.session.commit()
    return jsonify({'message': 'Test case deleted successfully'}), 200
