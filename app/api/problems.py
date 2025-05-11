from flask import Blueprint, request, jsonify
from app import db
from app.models import Problem, TestCase

problems_bp = Blueprint('problems_bp', __name__, url_prefix='/api/problems')

@problems_bp.route('', methods=['POST'])
def create_problem():
    data = request.get_json()
    if not data or not 'title' in data or not 'description' in data or not 'llm_prompt' in data:
        return jsonify({'message': 'Missing title, description, or llm_prompt'}), 400

    new_problem = Problem(
        title=data['title'],
        description=data['description'],
        llm_prompt=data['llm_prompt']
    )
    db.session.add(new_problem)
    db.session.commit()

    return jsonify({'message': 'Problem created successfully', 'problem': {'id': new_problem.id, 'title': new_problem.title, 'description': new_problem.description, 'llm_prompt': new_problem.llm_prompt}}), 201

@problems_bp.route('', methods=['GET'])
def get_problems():
    problems = Problem.query.all()
    problems_list = [{'id': problem.id, 'title': problem.title, 'description': problem.description, 'llm_prompt': problem.llm_prompt} for problem in problems]
    return jsonify(problems_list), 200

@problems_bp.route('/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    test_cases = [{'id': tc.id, 'input': tc.input, 'expected_output': tc.expected_output, 'is_public': tc.is_public} for tc in problem.test_cases]
    return jsonify({
        'id': problem.id,
        'title': problem.title,
        'description': problem.description,
        'llm_prompt': problem.llm_prompt,
        'test_cases': test_cases
    }), 200

@problems_bp.route('/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    if 'title' in data:
        problem.title = data['title']
    if 'description' in data:
        problem.description = data['description']
    if 'llm_prompt' in data:
        problem.llm_prompt = data['llm_prompt']

    db.session.commit()
    return jsonify({'message': 'Problem updated successfully', 'problem': {'id': problem.id, 'title': problem.title, 'description': problem.description, 'llm_prompt': problem.llm_prompt}}), 200

@problems_bp.route('/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    # Add logic to delete associated test cases and submissions if necessary
    # For now, just deleting the problem itself
    db.session.delete(problem)
    db.session.commit()
    return jsonify({'message': 'Problem deleted successfully'}), 200
