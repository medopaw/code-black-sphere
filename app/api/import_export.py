from flask import Blueprint, request, jsonify
from app import db
from app.models import Problem, TestCase
import json

import_export_bp = Blueprint('import_export_bp', __name__, url_prefix='/api')

@import_export_bp.route('/problems/import', methods=['POST'])
def import_problems():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and file.filename.endswith('.json'):
        try:
            problems_data = json.load(file)
        except json.JSONDecodeError:
            return jsonify({'message': 'Invalid JSON file'}), 400

        imported_count = 0
        updated_count = 0

        for problem_data in problems_data:
            name = problem_data.get('name')
            description = problem_data.get('description', '')
            llm_prompt = problem_data.get('llm_prompt', '')
            test_cases_data = problem_data.get('test_cases', [])

            if not name:
                # Skip if problem name is missing
                continue

            problem = Problem.query.filter_by(name=name).first()
            if problem:
                # Update existing problem
                problem.description = description
                problem.llm_prompt = llm_prompt
                # Clear existing test cases for simplicity, or implement more complex update logic
                TestCase.query.filter_by(problem_id=problem.id).delete()
                updated_count += 1
            else:
                # Create new problem
                problem = Problem(name=name, description=description, llm_prompt=llm_prompt)
                db.session.add(problem)
                imported_count += 1
            
            db.session.flush() # Ensure problem.id is available for new problems

            for tc_data in test_cases_data:
                input_data = tc_data.get('input')
                expected_output = tc_data.get('expected_output')
                is_public = tc_data.get('is_public', True)
                if input_data is not None and expected_output is not None:
                    test_case = TestCase(
                        problem_id=problem.id,
                        input=json.dumps(input_data), # Store as JSON string
                        expected_output=json.dumps(expected_output), # Store as JSON string
                        is_public=is_public
                    )
                    db.session.add(test_case)
        
        db.session.commit()
        return jsonify({
            'message': 'Problems imported successfully',
            'imported_count': imported_count,
            'updated_count': updated_count
        }), 200
    else:
        return jsonify({'message': 'Invalid file type, please upload a .json file'}), 400

@import_export_bp.route('/problems/export', methods=['GET'])
def export_problems():
    problems = Problem.query.all()
    problems_data = []
    for problem in problems:
        test_cases = TestCase.query.filter_by(problem_id=problem.id).all()
        test_cases_data = [
            {
                'input': json.loads(tc.input),
                'expected_output': json.loads(tc.expected_output),
                'is_public': tc.is_public
            } for tc in test_cases
        ]
        problems_data.append({
            'name': problem.name,
            'description': problem.description,
            'llm_prompt': problem.llm_prompt,
            'test_cases': test_cases_data
        })
    
    response = jsonify(problems_data)
    response.headers['Content-Disposition'] = 'attachment; filename=problems_export.json'
    response.mimetype = 'application/json'
    return response, 200
