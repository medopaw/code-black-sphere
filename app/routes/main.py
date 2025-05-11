from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Serve the main page with the code submission form."""
    return render_template('index.html', title='在线代码评测')

@main_bp.route('/hello') # Added a simple hello route as it was in base.html nav
def hello():
    return "Hello, World! This is a placeholder page."
