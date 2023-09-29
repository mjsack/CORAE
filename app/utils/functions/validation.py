from ...models import Project
from flask_login import current_user
from flask import abort

def allowed_file(filename, allowed_extensions):
    """
    Check if the given filename has an allowed extension.

    Parameters:
    - filename (str): The name of the file to be checked.
    - allowed_extensions (list): A list of allowed file extensions.

    Returns:
    - bool: True if the filename has an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_project_owner(project_id):
    """
    Validate if the current logged-in user is the owner of the specified project.

    Parameters:
    - project_id (int): The ID of the project to be checked.

    Raises:
    - 403 Forbidden: If the current user is not the owner of the project.
    """
    project = Project.query.get_or_404(project_id)
    if project.researcher != current_user:
        abort(403)
        
def validate_file_upload(file):
    """
    Validate the uploaded file based on its presence, filename, and type.

    Parameters:
    - file (FileStorage): The uploaded file object.

    Returns:
    - str: An error code indicating the type of validation error, or None if the file is valid.
    """
    if not file:
        return 'NO_FILE'
    if file.filename == '':
        return 'NO_SELECTED_FILE'
    if not allowed_file(file.filename):
        return 'INVALID_FILE_TYPE'
    return None
