import os
from flask import Flask
from app.config import Config
from app.database.db import init_db, close_db
from app.database.models import SettingsModel
from app.services.face_recognition import face_recognizer

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Initialize storage directories
    Config.init_app()

    
    # Database teardown
    app.teardown_appcontext(close_db)
    
    # Initialize Database Schema & Seed Initial Admin
    with app.app_context():
        init_db()
        # Initialize / reload recognizer model
        face_recognizer.load_model()
    
    # Register Route Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.recognition import recognition_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(recognition_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    
    # Global context processors for templates
    @app.context_processor
    def inject_global_vars():
        inst_name = SettingsModel.get('institution_name', 'University Department of Computer Science')
        return {
            'APP_NAME': 'FaceAttend',
            'APP_VERSION': '2.0.0 Pro',
            'INSTITUTION_NAME': inst_name,
            'IS_MODEL_TRAINED': face_recognizer.is_trained,
            'TOTAL_ENROLLED_FACES': len(face_recognizer.labels_map)
        }
        
    return app
