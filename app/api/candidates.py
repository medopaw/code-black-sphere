from flask import Blueprint, request, jsonify
from app import db
from app.models import Candidate
from werkzeug.security import generate_password_hash

candidates_bp = Blueprint('candidates_bp', __name__, url_prefix='/api')

@candidates_bp.route('/candidates', methods=['POST'])
def create_candidate():
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'email', 'password']):
        return jsonify({'message': 'Missing name or email'}), 400

    # 检查重复名称
    if Candidate.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Candidate name already exists'}), 409

    # 检查重复邮箱
    if Candidate.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Candidate with this email already exists'}), 409

    # 创建新候选人
    candidate = Candidate(
        name=data['name'],
        email=data['email']
    )
    candidate.set_password(data['password'])
    db.session.add(candidate)
    db.session.commit()

    return jsonify({
        'candidate': {
            'id': candidate.id,
            'name': candidate.name,
            'email': candidate.email
        }
    }), 201

@candidates_bp.route('/candidates', methods=['GET'])
def get_candidates():
    candidates = Candidate.query.all()
    candidates_list = [{'id': candidate.id, 'name': candidate.name, 'email': candidate.email} for candidate in candidates]
    return jsonify(candidates_list), 200

@candidates_bp.route('/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    return jsonify({'id': candidate.id, 'name': candidate.name, 'email': candidate.email}), 200

@candidates_bp.route('/candidates/<int:candidate_id>', methods=['PUT'])
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

@candidates_bp.route('/candidates/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    return jsonify({'message': 'Candidate deleted successfully'}), 200
