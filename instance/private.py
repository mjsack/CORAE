import os
from app.utils.constants import INSTANCE_FOLDER_PATH

CSRF_SESSION_KEY = "secret"
SECRET_KEY = "secret"

DB_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'database.db')

SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
