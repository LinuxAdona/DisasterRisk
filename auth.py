from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from models import User
from forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.approved:
            flash('Your account is pending approval. Please wait for an administrator to approve your account.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.role == 'admin':
                next_page = url_for('admin.dashboard')
            elif user.role == 'volunteer':
                next_page = url_for('volunteer.dashboard')
            else:  # donor
                next_page = url_for('donor.dashboard')
        
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.get_by_username(form.username.data):
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html', title='Register', form=form)
        
        if User.get_by_email(form.email.data):
            flash('Email already exists. Please use a different one.', 'danger')
            return render_template('register.html', title='Register', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        user.save()
        
        flash('Your account has been created. Please wait for administrator approval before logging in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', title='Register', form=form)
