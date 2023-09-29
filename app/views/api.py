from flask import Blueprint, flash, jsonify, redirect, request, url_for
from flask_login import login_required

from ..utils.functions.common import delete_item_from_db

api = Blueprint('api', __name__)

@api.route('/presets/<int:preset_id>/settings', methods=['GET'])
@login_required
def get_preset_settings(preset_id):
    """
    Fetch the settings associated with a given preset ID.

    Parameters:
    - preset_id (int): The ID of the preset whose settings are to be fetched.

    Returns:
    - JSON: A JSON representation of the preset's settings or an error message if the settings are not found.
    """
    from ..models import Preset
    preset = Preset.query.get_or_404(preset_id)
    settings = preset.settings
    if not settings:
        return jsonify({"error": "Settings not found for the given preset ID"}), 404
    return jsonify(settings.to_dict())

@api.route('/delete_item/<item_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_type, item_id):
    """
    Delete an item from the database based on its type and ID.

    Parameters:
    - item_type (str): The type of the item to be deleted (e.g., 'project', 'session').
    - item_id (int): The ID of the item to be deleted.

    Returns:
    - Redirect: Redirects the user to the dashboard or another specified URL after the item has been deleted.
    """
    success, message = delete_item_from_db(item_type, item_id)
    next_url = request.form.get('next', url_for('dashboard.dash'))
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(next_url)

