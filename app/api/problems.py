from flask import Blueprint, request, jsonify
from app import db
from app.models import Problem, TestCase

problems_bp = Blueprint('problems_bp', __name__, url_prefix='/api/problems')

@problems_bp.route('', methods=['POST'])
def create_problem():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('description') or not data.get('llm_prompt'):
        return jsonify({'message': 'Missing required fields: title, description, or llm_prompt'}), 400

    if Problem.query.filter_by(title=data['title']).first():
        return jsonify({'message': 'Problem title already exists'}), 400

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
    return jsonify({'problems': problems_list}), 200

@problems_bp.route('/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    # Assuming TestCase model has 'input_params' and 'expected_output' and 'is_public' might not exist or be relevant here
    # Adjust according to actual TestCase model structure and what needs to be exposed
    test_cases = [{'id': tc.id, 'input_params': tc.input_params, 'expected_output': tc.expected_output} for tc in problem.test_cases]
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

    if 'title' in data and data['title'] != problem.title:
        if Problem.query.filter(Problem.id != problem_id, Problem.title == data['title']).first():
            return jsonify({'message': 'Problem title already exists'}), 400
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
