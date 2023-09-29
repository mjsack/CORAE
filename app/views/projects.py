from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from ..forms import ArchiveForm, DeleteForm, ProjectCreateForm
from ..models import Preset, Project, Session, Settings, db
from ..utils.functions.common import parse_json_attributes, toggle_item_status

projects = Blueprint('projects', __name__)

@projects.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """
    Create a new project for the logged-in researcher.

    Returns:
    - Rendered Template: Displays the project creation form.
    - Response: Redirects to the dashboard after project creation.
    """
    current_app.logger.info(f"Creating a new project for researcher ID: {current_user.id}")
    form = ProjectCreateForm()
    form.preset.choices = [('new', 'New Configuration')] + [(p.id, p.name) for p in current_user.presets]

    if form.validate_on_submit():
        project = Project(name=form.name.data, description=form.description.data, researcher=current_user)
        project.tokenize()
        db.session.add(project)
        db.session.commit()
        preset = Preset.query.get(form.preset.data)

        if preset:
            current_app.logger.info(f"Using preset ID: {preset.id} for the new project")
            project.settings = parse_json_attributes(preset.settings)
        else:
            current_app.logger.info(f"Creating new settings for the new project")
            new_settings = Settings()
            for key, value in form.settings.data.items():
                setattr(new_settings, key, value)
            db.session.add(new_settings)
            db.session.flush()
            project.settings = new_settings

        db.session.add(project)
        db.session.commit()
        current_app.logger.info(f"Project ID: {project.id} created successfully")
        flash('Project created successfully!')
        return redirect(url_for('dashboard.dash', project_id=project.id))
    current_app.logger.warning(f"Form validation failed for new project for researcher: {current_user.username}")
    return render_template('admin/projects/new_project.html', title='New Project', header='New Project', form=form, form_action='/admin/projects/new')


@projects.route('/projects/<int:project_id>', methods=['GET', 'POST'])
@login_required
def view_project(project_id):
    """
    View details of a specific project.

    Parameters:
    - project_id (int): ID of the project to view.

    Returns:
    - Rendered Template: Displays the project details.
    """
    current_app.logger.info(f"Viewing project ID: {project_id} for user ID: {current_user.id}")
    project = Project.query.get_or_404(project_id)
    sessions = project.sessions.all()

    delete_form = DeleteForm()
    if delete_form.validate_on_submit():
        session_to_delete = Session.query.get_or_404(request.form.get('session_id'))
        current_app.logger.info(f"Deleting session ID: {session_to_delete.id} for project ID: {project_id}")
        session_to_delete.delete_from_db()
        flash('Session deleted successfully.')
        return redirect(url_for('dashboard.dash'))
    
    archive_form = ArchiveForm()
    if archive_form.validate_on_submit():
        session_to_toggle = Session.query.get_or_404(request.form.get('session_id'))
        current_app.logger.info(f"Toggling status for session ID: {session_to_toggle.id} for project ID: {project_id}")
        toggle_item_status('session', session_to_toggle.id)

    for session in sessions:
        current_app.logger.debug(f"Session {session.id} has participants: {', '.join([p.name for p in session.participants])}")
    return render_template('admin/projects/view_project.html', title=project.name, header='Project', subheader=project.name, project=project, delete_form=delete_form, archive_form=archive_form, sessions=sessions)