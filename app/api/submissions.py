from flask import Blueprint, request, jsonify
from app import db
from app.models import Submission, Candidate, Problem # Assuming these models exist

submissions_bp = Blueprint('submissions_bp', __name__, url_prefix='/api')

@submissions_bp.route('/submissions', methods=['POST'])
def submit_solution():
    data = request.get_json()
    if not data or not all(k in data for k in ['candidate_id', 'problem_id', 'language', 'code']):
        return jsonify({'message': 'Missing required fields: candidate_id, problem_id, language, code'}), 400

    candidate = Candidate.query.get(data['candidate_id'])
    if not candidate:
        return jsonify({'message': 'Candidate not found'}), 404

    problem = Problem.query.get(data['problem_id'])
    if not problem:
        return jsonify({'message': 'Problem not found'}), 404

    # For now, we'll skip actual code execution and LLM review
    # These will be implemented in later stages (tasks 1.4 and 1.5)
    new_submission = Submission(
        candidate_id=data['candidate_id'],
        problem_id=data['problem_id'],
        language=data['language'],
        code=data['code'],
        # test_results will be populated after code execution
        # llm_review will be populated after LLM evaluation
    )
    db.session.add(new_submission)
    db.session.commit()

    return jsonify({
        'message': 'Submission received successfully. Evaluation pending.',
        'submission': {
            'id': new_submission.id,
            'candidate_id': new_submission.candidate_id,
            'problem_id': new_submission.problem_id,
            'language': new_submission.language,
            'submission_time': new_submission.submission_time.isoformat() # Ensure datetime is serializable
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
