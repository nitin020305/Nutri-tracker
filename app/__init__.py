from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config

db      = SQLAlchemy()
migrate = Migrate()
jwt     = JWTManager()

def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    from app.routes.auth      import auth_bp
    from app.routes.user      import user_bp
    from app.routes.food      import food_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(user_bp,      url_prefix="/api/user")
    app.register_blueprint(food_bp,      url_prefix="/api/food")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.route("/")
    def index():
        import os
        from flask import send_from_directory
        template_dir = os.path.join(app.root_path, "templates")
        return send_from_directory(template_dir, "index.html")

    return app
