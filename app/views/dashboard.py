from flask import Blueprint, current_app, render_template
from flask_login import current_user, login_required

from ..forms import DeleteForm

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard')
@login_required
def dash():
    """
    Display the main dashboard for the logged-in researcher.

    Returns:
    - Rendered Template: Displays the dashboard with a list of projects, presets, and other related information.
    """
    form = DeleteForm()
    projects = current_user.projects
    presets = current_user.presets

    if not projects:
        current_app.logger.debug("projects is None or Empty")
    if not presets:
        current_app.logger.debug("presets is None or Empty")
    if not current_user:
        current_app.logger.debug("current_user is None")

    for project in projects:
        current_app.logger.debug(f"Project Name: {project.name}")
        current_app.logger.debug(f"Project Settings: {project.settings}")
        if project.settings:
            current_app.logger.debug(f"Project Settings Dict: {project.settings.to_dict()}")

    return render_template('admin/index.html', title='Dashboard', header='Dashboard', subheader=current_user.username, projects=projects, presets=presets, form=form)

@dashboard.route('/analytics')
@login_required
def analytics():
    """
    Display the analytics page for the logged-in researcher.

    Returns:
    - Rendered Template: Displays the analytics page with a list of projects and related analytics.
    """
    projects = current_user.projects
    return render_template('admin/analytics.html', title='Analytics', header='Analytics', projects=projects)

