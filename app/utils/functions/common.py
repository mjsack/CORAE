import os, json
import importlib
from datetime import datetime
from ..extensions import db

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'flv', 'mkv'}

def get_item_model(item_type):
    """
    Dynamically import and return the model class based on the given item type.

    Parameters:
    - item_type (str): The type of the item (e.g., 'project', 'session').

    Returns:
    - class: The corresponding model class or None if not found.
    """
    try:
        module_name = "..models"
        module = importlib.import_module(module_name, package="app.utils")
        return getattr(module, item_type.capitalize())
    except Exception as e:
        raise e

def get_current_time():
    """
    Get the current UTC time.

    Returns:
    - datetime: The current UTC time.
    """
    return datetime.utcnow()

def allowed_file(filename):
    """
    Check if the given filename has an allowed extension.

    Parameters:
    - filename (str): The name of the file to be checked.

    Returns:
    - bool: True if the filename has an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def make_dir(dir_path):
    """
    Create a directory if it doesn't exist.

    Parameters:
    - dir_path (str): The path of the directory to be created.
    """
    try:
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
    except Exception as e:
        raise e

def get_item_by_id(item_type, item_id):
    """
    Retrieve an item from the database based on its type and ID.

    Parameters:
    - item_type (str): The type of the item (e.g., 'project', 'session').
    - item_id (int): The ID of the item.

    Return:
    - obj: The retrieved item or None if not found.
    """
    model = get_item_model(item_type)
    if not model:
        return None
    return model.query.get_or_404(item_id)

def delete_item_from_db(item_type, item_id):
    """
    Delete an item from the database based on its type and ID.

    Parameters:
    - item_type (str): The type of the item (e.g., 'project', 'session').
    - item_id (int): The ID of the item.

    Returns:
    - tuple: A tuple containing a boolean indicating success or failure, and a message string.
    """
    model = get_item_model(item_type)
    if not model:
        return False, 'Invalid item type!'
    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    return True, f'{item_type.capitalize()} deleted successfully!'

def toggle_item_status(item_type, item_id):
    """
    Toggle the status (active/archived) of an item.

    Parameters:
    - item_type (str): The type of the item (e.g., 'project', 'session').
    - item_id (int): The ID of the item.

    Note:
    - This function assumes that the item has a 'status' attribute that can be either 'active' or 'archived'.
    """
    model = get_item_model(item_type)
    item = model.query.get_or_404(item_id)
    item.status = 'archived' if item.status == 'active' else 'active'
    db.session.commit()
    
def load_settings(objs):
    """
    Load settings for a list of objects and parse JSON values if present.

    Parameters:
    - objs (list): A list of objects that have a 'settings' attribute.

    Returns:
    - list: The list of objects with parsed settings.
    """
    for obj in objs:
        settings = obj.settings
        if isinstance(settings.value, str):
            try:
                settings.value = json.loads(settings.value)
            except json.JSONDecodeError:
                pass
    return objs

def parse_json_attributes(settings):
    """
    Parse JSON attributes of a settings object.

    Parameters:
    - settings (object): The settings object with attributes that may contain JSON strings.

    Returns:
    - object: The settings object with parsed attributes.
    """
    for attr in dir(settings):
        if attr.startswith("__") or callable(getattr(settings, attr)):
            continue
        value = getattr(settings, attr)
        if isinstance(value, str):
            try:
                parsed_value = json.loads(value)
                setattr(settings, attr, parsed_value)
            except json.JSONDecodeError:
                pass
    return settings