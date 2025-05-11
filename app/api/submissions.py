from flask import Blueprint, request, jsonify, current_app
from app.services.judge0_service import Judge0Service
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

    # Map language string to Judge0 language ID
    # This is a simplified mapping. A more robust solution would be needed for production.
    language_mapping = {
        "python": 71,  # Python 3.8.1
        "javascript": 63, # Node.js 12.14.0
        "java": 62, # Java OpenJDK 13.0.1
        "c++": 54, # C++ GCC 9.2.0
        # Add other common languages and their Judge0 IDs
    }
    language_str = data['language'].lower()
    language_id = language_mapping.get(language_str)

    if language_id is None:
        return jsonify({'message': f'Unsupported language: {data["language"]}. Supported: {list(language_mapping.keys())}'}), 400

    judge0_service = Judge0Service()

    # TODO: Get stdin and expected_output from the Problem model if available
    # For now, using None, which Judge0Service handles with defaults or empty values.
    problem_stdin = None # problem.stdin if hasattr(problem, 'stdin') else None
    # problem_expected_output = None # problem.expected_output if hasattr(problem, 'expected_output') else None

    # Get optional resource limits from request, or use Judge0Service defaults (which are None, meaning Judge0's defaults)
    cpu_time_limit = data.get('cpu_time_limit') # Optional: float, in seconds
    memory_limit = data.get('memory_limit')     # Optional: int, in kilobytes

    submission_token = judge0_service.submit_code(
        source_code=data['code'],
        language=language_id, # Use language_id (integer) here
        stdin=problem_stdin,
        # expected_output=problem_expected_output # Add if test cases have expected output
        cpu_time_limit=cpu_time_limit,
        memory_limit=memory_limit
    )

    if not submission_token:
        return jsonify({'message': 'Failed to submit code to execution service.'}), 500

    # Wait for the submission to complete
    # Timeout and poll interval can be configured in Judge0Service or passed here
    results = judge0_service.wait_for_submission(submission_token)

    if not results:
        # Attempt to create submission record even if Judge0 polling failed/timed out, with an error status
        new_submission = Submission(
            candidate_id=data['candidate_id'],
            problem_id=data['problem_id'],
            language=data['language'],
            code=data['code'],
            status="Error during execution or timeout",
            test_results={'error': 'Failed to retrieve execution results from Judge0.'}
        )
        db.session.add(new_submission)
        db.session.commit()
        current_app.logger.error(f"Failed to get results for Judge0 token: {submission_token}")
        return jsonify({'message': 'Code submitted, but failed to retrieve execution results in time.', 'submission_id': new_submission.id}), 500

    # Process results
    status_description = results.get('status', {}).get('description', 'Unknown Status')
    stdout = results.get('stdout')
    stderr = results.get('stderr')
    compile_output = results.get('compile_output')
    exec_time = results.get('time')
    memory_used = results.get('memory')

    new_submission = Submission(
        candidate_id=data['candidate_id'],
        problem_id=data['problem_id'],
        language=data['language'], # Store original language string
        code=data['code'],
        status=status_description,
        test_results={
            'stdout': stdout,
            'stderr': stderr,
            'compile_output': compile_output,
            'time': exec_time,
            'memory': memory_used,
            'judge0_status_id': results.get('status', {}).get('id'),
            'judge0_token': submission_token,
            'cpu_time_limit_requested': cpu_time_limit, # Store requested limits for reference
            'memory_limit_requested': memory_limit      # Store requested limits for reference
        }
        # llm_review will be populated later
    )
    db.session.add(new_submission)
    db.session.commit()

    return jsonify({
        'message': f'Submission processed. Status: {status_description}',
        'submission': {
            'id': new_submission.id,
            'candidate_id': new_submission.candidate_id,
            'problem_id': new_submission.problem_id,
            'language': new_submission.language,
            'submission_time': new_submission.submission_time.isoformat(),
            'status': new_submission.status,
            'test_results': new_submission.test_results
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
