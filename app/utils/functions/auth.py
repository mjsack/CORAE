import json
from flask import current_app, abort
from flask_login import current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ...models import Researcher
from ..extensions import db

def register_user(username, password):
    """
    Register a new user in the system.

    Parameters:
    - username (str): The desired username for the new user.
    - password (str): The desired password for the new user.

    Returns:
    - tuple: A tuple containing a boolean indicating success or failure, and a message string.
    """
    current_app.logger.info(f"Attempting to register user: {username}")
    researcher = Researcher(username=username, password=password)
    try:
        db.session.add(researcher)
        db.session.commit()
        current_app.logger.info(f"User {username} registered successfully.")
        return True, 'Registration successful!'
    except IntegrityError:
        db.session.rollback()
        current_app.logger.warning(f"Username {username} already exists.")
        return False, 'Username already exists!'
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error(f"Database error occurred during registration for user: {username}")
        return False, 'Registration failed due to a database error!'

def authenticate_user(username, password):
    """
    Authenticate a user based on their username and password.

    Parameters:
    - username (str): The username of the user attempting to log in.
    - password (str): The password of the user attempting to log in.

    Returns:
    - tuple: A tuple containing the authenticated user object (or None if authentication fails) and a message string.
    """
    researcher = Researcher.query.filter_by(username=username).first()
    if researcher and researcher.verify_password(password):
        return researcher, 'Login successful!'
    return None, 'Invalid username or password.'
