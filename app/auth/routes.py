from flask import render_template, redirect, url_for, flash
from app import db
from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, current_user, login_required
from app.models import Candidate

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        candidate = Candidate(name=form.username.data, email=form.email.data)
        candidate.set_password(form.password.data)
        db.session.add(candidate)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login')) # Redirect to login page after successful registration
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.hello')) # Or wherever you want to redirect logged-in users
    form = LoginForm()
    if form.validate_on_submit():
        user = Candidate.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.hello')) # Or a user profile page
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.hello')) # Or the main index page
