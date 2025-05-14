from flask import Blueprint, request, jsonify
from app import db
from app.models import Candidate, Problem, CandidateProblemTab

tabs_bp = Blueprint('tabs_bp', __name__, url_prefix='/api')

@tabs_bp.route('/candidates/<int:candidate_id>/tabs', methods=['POST'])
def add_tab(candidate_id):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return jsonify({'message': 'Candidate not found'}), 404
    
    data = request.get_json()
    if not data or 'problem_id' not in data:
        return jsonify({'message': 'Missing problem_id in request body'}), 400
    
    problem = db.session.get(Problem, data['problem_id'])
    if not problem:
        return jsonify({'message': 'Problem not found'}), 404
    
    # 检查是否已存在相同的标签
    existing_tab = CandidateProblemTab.query.filter_by(
        candidate_id=candidate_id,
        problem_id=data['problem_id']
    ).first()
    if existing_tab:
        return jsonify({'message': 'Tab for this problem already exists'}), 400
    
    # 获取当前最大的tab_order
    max_order = db.session.query(db.func.max(CandidateProblemTab.tab_order)).filter_by(candidate_id=candidate_id).scalar() or 0
    
    new_tab = CandidateProblemTab(
        candidate_id=candidate_id,
        problem_id=data['problem_id'],
        tab_order=max_order + 1
    )
    db.session.add(new_tab)
    db.session.commit()
    
    return jsonify({
        'tab': {
            'id': new_tab.id,
            'candidate_id': new_tab.candidate_id,
            'problem_id': new_tab.problem_id,
            'tab_order': new_tab.tab_order
        }
    }), 201

@tabs_bp.route('/candidates/<int:candidate_id>/tabs', methods=['GET'])
def get_candidate_tabs(candidate_id):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return jsonify({'message': 'Candidate not found'}), 404
    
    tabs = CandidateProblemTab.query.filter_by(candidate_id=candidate_id).order_by(CandidateProblemTab.tab_order).all()
    return jsonify({
        'tabs': [{
            'id': tab.id,
            'problem_id': tab.problem_id,
            'tab_order': tab.tab_order
        } for tab in tabs]
    })

@tabs_bp.route('/candidates/<int:candidate_id>/tabs', methods=['PUT'])
def update_tab_order(candidate_id):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return jsonify({'message': 'Candidate not found'}), 404
    
    data = request.get_json()
    if not data or 'ordered_problem_ids' not in data:
        return jsonify({'message': 'Missing ordered_problem_ids field'}), 400
    
    # 获取当前标签
    current_tabs = CandidateProblemTab.query.filter_by(candidate_id=candidate_id).all()
    current_problem_ids = {tab.problem_id for tab in current_tabs}
    requested_problem_ids = set(data['ordered_problem_ids'])
    
    # 验证问题ID是否匹配
    if current_problem_ids != requested_problem_ids:
        if requested_problem_ids - current_problem_ids:
            return jsonify({'message': 'contains problem IDs not currently in the candidate tabs'}), 400
        else:
            return jsonify({'message': 'The set of problem IDs in the request does not match the set of current tabs'}), 400
    
    # 更新标签顺序
    for order, problem_id in enumerate(data['ordered_problem_ids'], 1):
        tab = next(tab for tab in current_tabs if tab.problem_id == problem_id)
        tab.tab_order = order
    
    db.session.commit()
    
    # 获取更新后的标签列表
    updated_tabs = CandidateProblemTab.query.filter_by(candidate_id=candidate_id).order_by(CandidateProblemTab.tab_order).all()
    
    return jsonify({
        'tabs': [{
            'id': tab.id,
            'candidate_id': tab.candidate_id,
            'problem_id': tab.problem_id,
            'tab_order': tab.tab_order
        } for tab in updated_tabs]
    })

@tabs_bp.route('/candidates/<int:candidate_id>/tabs/<int:problem_id>', methods=['DELETE'])
def remove_tab(candidate_id, problem_id):
    candidate = db.session.get(Candidate, candidate_id)
    if not candidate:
        return jsonify({'message': 'Candidate not found'}), 404
    
    tab = CandidateProblemTab.query.filter_by(
        candidate_id=candidate_id,
        problem_id=problem_id
    ).first()
    
    if not tab:
        return jsonify({'message': 'Tab not found'}), 404
    
    db.session.delete(tab)
    db.session.commit()
    
    return jsonify({'message': 'Tab removed successfully'})
