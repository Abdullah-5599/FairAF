from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate                       # <-- Required for Flask-Migrate

from .models import db, User
from .auth.routes import auth_bp
from .main.routes import main_bp
from .chore.routes import chore_bp
from .expense.routes import expense_bp
from .main.group_fund_routes import group_fund_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key-change-me'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/fairaf.db'
    app.config['UPLOAD_FOLDER'] = 'FairAF/static/uploads'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    migrate = Migrate(app, db)                         # <-- REQUIRED

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chore_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(group_fund_bp)

    return app
