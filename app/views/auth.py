from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from ..forms import LoginForm, RegisterForm
from ..utils.functions.auth import authenticate_user, register_user

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    If the registration is successful, the user is logged in and redirected to the dashboard.

    Returns:
    - Rendered Template: Displays the registration form or redirects to the dashboard upon successful registration.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        success, message = register_user(form.username.data, form.password.data)
        user, message = authenticate_user(form.username.data, form.password.data)
        flash(message)
        if success:
            if user:
                login_user(user)
                return redirect(request.args.get('next') or url_for('dashboard.dash'))
    return render_template('register.html', title='Register', header='Register', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    If the login is successful, the user is redirected to the dashboard.

    Returns:
    - Rendered Template: Displays the login form or redirects to the dashboard upon successful login.
    """
    form = LoginForm()
    if form.validate_on_submit():
        user, message = authenticate_user(form.username.data, form.password.data)
        flash(message)
        if user:
            login_user(user)
            return redirect(request.args.get('next') or url_for('dashboard.dash'))
    return render_template('login.html', title='Login', header='Login', form=form)

@auth.route('/logout')
@login_required
def logout():
    """
    Handle user logout.
    After logging out, the user is redirected to the home page.

    Returns:
    - Redirect: Redirects the user to the home page after logging out.
    """
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('core.index'))
