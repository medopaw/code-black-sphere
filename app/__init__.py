from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # login_manager.login_view = 'auth.login' # Specifies the endpoint for the login page

    # Register blueprints here
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    from app.api.candidates import candidates_bp
    app.register_blueprint(candidates_bp)

    from app.api.problems import problems_bp
    app.register_blueprint(problems_bp)

    from app.api.test_cases import test_cases_bp
    app.register_blueprint(test_cases_bp)

    from app.api.submissions import submissions_bp
    app.register_blueprint(submissions_bp)

    from app.api.tabs import tabs_bp
    app.register_blueprint(tabs_bp)

    from app.api.settings import settings_bp
    app.register_blueprint(settings_bp)

    from app.api.import_export import import_export_bp
    app.register_blueprint(import_export_bp)



    from app.models import Candidate # Import Candidate model for user_loader
    @login_manager.user_loader
    def load_user(user_id):
        return Candidate.query.get(int(user_id))

    return app
