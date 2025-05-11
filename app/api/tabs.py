from flask import Blueprint, request, jsonify
from app import db
from app.models import Candidate, Problem, CandidateProblemTab

tabs_bp = Blueprint('tabs_bp', __name__, url_prefix='/api')

@tabs_bp.route('/candidates/<int:candidate_id>/tabs', methods=['POST'])
def add_candidate_tab(candidate_id):
    data = request.get_json()
    if not data or 'problem_id' not in data:
        return jsonify({'message': 'Missing problem_id in request body'}), 400

    problem_id = data['problem_id']

    candidate = Candidate.query.get_or_404(candidate_id)
    problem = Problem.query.get_or_404(problem_id)

    # Check if the tab already exists for this candidate and problem
    existing_tab = CandidateProblemTab.query.filter_by(candidate_id=candidate_id, problem_id=problem_id).first()
    if existing_tab:
        return jsonify({'message': 'Tab already exists for this candidate and problem', 'tab_id': existing_tab.id}), 200 # Or 409 Conflict

    new_tab = CandidateProblemTab(
        candidate_id=candidate_id,
        problem_id=problem_id
        # code and other fields can be added/updated later if needed
    )
    db.session.add(new_tab)
    db.session.commit()

    return jsonify({
        'message': 'Tab added successfully',
        'tab': {
            'id': new_tab.id,
            'candidate_id': new_tab.candidate_id,
            'problem_id': new_tab.problem_id
        }
    }), 201

@tabs_bp.route('/candidates/<int:candidate_id>/tabs', methods=['GET'])
def get_candidate_tabs(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)

    tabs = CandidateProblemTab.query.filter_by(candidate_id=candidate_id).all()

    if not tabs:
        return jsonify({'message': 'No tabs found for this candidate', 'tabs': []}), 200

    problem_ids = [tab.problem_id for tab in tabs]

    return jsonify({'candidate_id': candidate_id, 'tabs': problem_ids}), 200

@tabs_bp.route('/candidates/<int:candidate_id>/tabs/<int:problem_id>', methods=['DELETE'])
def remove_candidate_tab(candidate_id, problem_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    problem = Problem.query.get_or_404(problem_id) # Ensure problem exists, though not strictly necessary for deletion if tab exists

    tab_to_delete = CandidateProblemTab.query.filter_by(candidate_id=candidate_id, problem_id=problem_id).first()

    if not tab_to_delete:
        return jsonify({'message': 'Tab not found for this candidate and problem'}), 404

    db.session.delete(tab_to_delete)
    db.session.commit()

    return jsonify({'message': 'Tab removed successfully'}), 200

@tabs_bp.route('/candidates/<int:candidate_id>/tabs', methods=['PUT'])
def update_candidate_tab_order(candidate_id):
    data = request.get_json()
    if not data or 'tabs' not in data:
        return jsonify({'message': 'Missing tabs data in request body'}), 400

    tabs_data = data['tabs'] # Expected: a list of problem_ids in the new order

    candidate = Candidate.query.get_or_404(candidate_id)

    # Fetch existing tabs for the candidate
    existing_tabs = CandidateProblemTab.query.filter_by(candidate_id=candidate_id).all()
    existing_tabs_map = {tab.problem_id: tab for tab in existing_tabs}

    if len(tabs_data) != len(existing_tabs):
        # This could mean either new tabs are being added, or some are missing.
        # For simplicity, this endpoint will only reorder existing tabs.
        # If tabs need to be added/removed, use the POST/DELETE endpoints.
        return jsonify({'message': 'The number of provided tabs does not match existing tabs. This endpoint only reorders.'}), 400

    # Validate that all problem_ids in tabs_data exist for the candidate
    for problem_id_in_order in tabs_data:
        if problem_id_in_order not in existing_tabs_map:
            return jsonify({'message': f'Problem ID {problem_id_in_order} not found in existing tabs for this candidate.'}), 404

    # Update the order
    for index, problem_id_in_order in enumerate(tabs_data):
        tab_to_update = existing_tabs_map[problem_id_in_order]
        tab_to_update.order = index # Assuming 'order' field exists and is 0-indexed
    
    db.session.commit()

    # Fetch updated tabs to return them in the new order
    updated_tabs_ordered = CandidateProblemTab.query.filter_by(candidate_id=candidate_id).order_by(CandidateProblemTab.order).all()
    ordered_problem_ids = [tab.problem_id for tab in updated_tabs_ordered]

    return jsonify({'message': 'Tabs order updated successfully', 'candidate_id': candidate_id, 'tabs': ordered_problem_ids}), 200
