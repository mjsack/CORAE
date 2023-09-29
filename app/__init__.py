from flask import Flask
from .utils.extensions import db, csrf, login_manager
from .views import *
from .config import DefaultConfig
import logging, os
import logging.handlers

def create_app(config=None):
        
    app = Flask(__name__, instance_relative_config=True)
    configure_app(app, config)
    configure_blueprints(app)
    configure_extensions(app)
    configure_logging(app)
    configure_error_handlers(app)
    configure_db(app)

    return app

def configure_app(app, config=None):
    app.config.from_object(DefaultConfig)
    
    app.config.from_pyfile('private.py', silent=True)
    
    if config:
        app.config.from_object(config)
        
def configure_extensions(app):
    
    csrf.init_app(app)
    
    db.init_app(app)
    
    login_manager.init_app(app)
    
def configure_blueprints(app):

    app.register_blueprint(core)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/admin')
    app.register_blueprint(projects, url_prefix='/admin')
    app.register_blueprint(presets, url_prefix='/admin')
    app.register_blueprint(sessions, url_prefix='/admin')
    app.register_blueprint(participant)
    app.register_blueprint(api, url_prefix='/api')
        
def configure_logging(app):
    if app.debug or app.testing:
        return
    
    app.logger.setLevel(logging.INFO)

    if not os.path.exists(app.config['LOGS_FOLDER_PATH']):
        app.logger.debug(f"{app.config['LOGS_FOLDER_PATH']} does not exist. Creating directory.")
        os.makedirs(app.config['LOGS_FOLDER_PATH'])
    info_log = os.path.join(app.config['LOGS_FOLDER_PATH'], 'info.log')
    info_file_handler = logging.handlers.RotatingFileHandler(info_log, maxBytes=100000, backupCount=10)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(info_file_handler)

    
def configure_error_handlers(app):

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404
    
def configure_db(app):
    with app.app_context():
        db.create_all()