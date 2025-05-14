from flask import Blueprint, jsonify, request
from app import db
from app.models import Setting

settings_bp = Blueprint('settings_bp', __name__, url_prefix='/api')

@settings_bp.route('/settings', methods=['GET'])
def get_all_settings():
    settings = Setting.query.all()
    return jsonify({
        'settings': [{
            'key': setting.key,
            'value': setting.value
        } for setting in settings]
    })

@settings_bp.route('/settings/<string:key>', methods=['GET'])
def get_setting(key):
    setting = Setting.query.get(key)
    if not setting:
        return jsonify({'message': 'Setting not found'}), 404
    return jsonify({
        'key': setting.key,
        'value': setting.value
    }), 200

@settings_bp.route('/settings/<string:key>', methods=['PUT'])
def update_setting(key):
    if not key or not key.strip():
        return jsonify({'message': 'Setting key cannot be empty'}), 400

    data = request.get_json()
    if not data or 'value' not in data:
        return jsonify({'message': 'Missing value field'}), 400

    setting = Setting.query.get(key)
    if setting:
        setting.value = data['value']
        status_code = 200
    else:
        setting = Setting(key=key, value=data['value'])
        db.session.add(setting)
        status_code = 201

    db.session.commit()
    return jsonify({
        'setting': {
            'key': setting.key,
            'value': setting.value
        }
    }), status_code
