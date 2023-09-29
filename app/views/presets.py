from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from ..forms import DeleteForm, PresetCreateForm
from ..models import Preset, Settings, db
from ..utils.functions.common import load_settings, parse_json_attributes

presets = Blueprint('presets', __name__)


@presets.route('/presets')
@login_required
def preset_list():
    """
    List all the presets available for the logged-in researcher.

    Returns:
    - Rendered Template: Displays the list of presets.
    """
    presets = load_settings(current_user.presets)
    return render_template('admin/presets/index.html', title='Presets', header='Presets', presets=presets)

@presets.route('/presets/new', methods=['GET', 'POST'])
@login_required
def new_preset():
    """
    Create a new preset for the logged-in researcher.

    Returns:
    - Rendered Template: Displays the preset creation form.
    - Response: Redirects to the dashboard after preset creation.
    """
    form = PresetCreateForm()
    
    if form.validate_on_submit():
        preset = Preset(name=form.name.data, description=form.description.data, researcher=current_user)
        preset_settings = Settings()
        for key, default_value in Settings.default_values().items():
            setattr(preset_settings, key, form.settings.data.get(key, default_value))
        
        preset.settings = parse_json_attributes(preset_settings)
        db.session.add(preset)
        db.session.commit()

        if preset.id:
            flash('Preset created successfully!')
            return redirect(url_for('dashboard.dash', preset_id=preset.id))
        else:
            flash('There was an error saving the preset. Please try again.', 'danger')
            return render_template('admin/presets/new_preset.html', title='New Preset', header='New Preset', form=form, form_action='/admin/presets/new')

    elif request.method == "GET":
        return render_template('admin/presets/new_preset.html', title='New Preset', header='New Preset', form=form, form_action='/admin/presets/new')

@presets.route('/presets/<int:preset_id>', methods=['GET', 'POST'])
@login_required
def edit_preset(preset_id):
    """
    Edit details of a specific preset.

    Parameters:
    - preset_id (int): ID of the preset to edit.

    Returns:
    - Rendered Template: Displays the preset edit form.
    - Response: Redirects to the dashboard after preset update.
    """
    preset = Preset.query.get_or_404(preset_id)
    
    if request.method == "POST":
        form = PresetCreateForm(request.form)
        if form.validate():
            preset.name = form.name.data
            preset.description = form.description.data
            preset_settings = Settings()
            for key, default_value in Settings.default_values().items():
                setattr(preset_settings, key, form.settings.data.get(key, default_value))

            preset.settings = parse_json_attributes(preset_settings)
            db.session.commit()

            flash('Preset updated successfully!')
            return redirect(url_for('dashboard.dash'))
        else:
            flash('There was an error updating the preset. Please double-check your changes.', 'danger')
    else:
        form_data = {
            'name': preset.name,
            'description': preset.description,
            'settings': preset.settings.to_dict()
        }
        form = PresetCreateForm(data=form_data)

    delete_form = DeleteForm()
    if delete_form.validate_on_submit():
        preset.delete_from_db()
        flash('Preset deleted successfully.')
        return redirect(url_for('dashboard.dash'))
    
    current_app.logger.debug(preset.settings.to_dict())
    return render_template('admin/presets/edit_preset.html', title=preset.name, header='Edit Preset', subheader=preset.name, preset=preset, form=form, delete_form=delete_form, edit_preset=True)