from flask import Blueprint, request, jsonify
from app import db
from app.models import Candidate

candidates_bp = Blueprint('candidates_bp', __name__, url_prefix='/api/candidates')

@candidates_bp.route('', methods=['POST'])
def create_candidate():
    data = request.get_json()
    if not data or not 'name' in data or not 'email' in data:
        return jsonify({'message': 'Missing name or email'}), 400

    if Candidate.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Candidate with this email already exists'}), 409

    new_candidate = Candidate(name=data['name'], email=data['email'])
    db.session.add(new_candidate)
    db.session.commit()

    return jsonify({'message': 'Candidate created successfully', 'candidate': {'id': new_candidate.id, 'name': new_candidate.name, 'email': new_candidate.email}}), 201

@candidates_bp.route('', methods=['GET'])
def get_candidates():
    candidates = Candidate.query.all()
    candidates_list = [{'id': candidate.id, 'name': candidate.name, 'email': candidate.email} for candidate in candidates]
    return jsonify(candidates_list), 200

@candidates_bp.route('/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    return jsonify({'id': candidate.id, 'name': candidate.name, 'email': candidate.email}), 200

@candidates_bp.route('/<int:candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    if 'name' in data:
        candidate.name = data['name']
    if 'email' in data:
        # Check if the new email already exists for another candidate
        existing_candidate = Candidate.query.filter(Candidate.id != candidate_id, Candidate.email == data['email']).first()
        if existing_candidate:
            return jsonify({'message': 'Email already in use by another candidate'}), 409
        candidate.email = data['email']

    db.session.commit()
    return jsonify({'message': 'Candidate updated successfully', 'candidate': {'id': candidate.id, 'name': candidate.name, 'email': candidate.email}}), 200

@candidates_bp.route('/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    return jsonify({'message': 'Candidate deleted successfully'}), 200
