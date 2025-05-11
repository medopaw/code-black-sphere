from flask import Blueprint, jsonify
from app import db
from app.models import Setting

settings_bp = Blueprint('settings_bp', __name__, url_prefix='/api')

@settings_bp.route('/settings', methods=['GET'])
def get_all_settings():
    settings = Setting.query.all()
    settings_dict = {setting.key: setting.value for setting in settings}
    return jsonify(settings_dict), 200

@settings_bp.route('/settings/<string:key>', methods=['GET'])
def get_setting_by_key(key):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        return jsonify({setting.key: setting.value}), 200
    else:
        return jsonify({'message': f'Setting with key "{key}" not found'}), 404

@settings_bp.route('/settings/<string:key>', methods=['PUT'])
def update_or_create_setting(key):
    data = request.get_json()
    if not data or 'value' not in data:
        return jsonify({'message': 'Missing value in request body'}), 400

    value = data['value']

    setting = Setting.query.filter_by(key=key).first()

    if setting:
        # Update existing setting
        setting.value = value
        # TODO: Add encryption for API keys if key is 'deepseek_api_key' or similar
    else:
        # Create new setting
        setting = Setting(key=key, value=value)
        # TODO: Add encryption for API keys if key is 'deepseek_api_key' or similar
        db.session.add(setting)
    
    db.session.commit()
    return jsonify({setting.key: setting.value}), 200
