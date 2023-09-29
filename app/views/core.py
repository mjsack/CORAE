from flask import Blueprint, render_template

core = Blueprint('core', __name__)


@core.route('/')
@core.route('/index')
def index():
    """
    Display the home page of the application.

    Returns:
    - Rendered Template: Displays the home page.
    """
    return render_template('index.html', title='Home')

@core.route('/docs')
def documentation():
    """
    Display the documentation page of the application.

    Returns:
    - Rendered Template: Displays the documentation page.
    """
    return render_template('documentation.html', title='Documentation', header='Documentation')

