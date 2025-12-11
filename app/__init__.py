from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import DevelopmentConfig as Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        db.create_all()
        # Ensure default admin user exists
        from app.models import User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True, is_approved=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

    return app
