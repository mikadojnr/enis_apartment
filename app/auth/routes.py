from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import auth_bp
from app import db
from app.models import User
from app.auth.forms import LoginForm, RegisterForm


def get_user_dashboard_url():
    """
    Helper to decide where to redirect after login/register
    - Admin → admin dashboard
    - Regular user → bookings dashboard
    """
    if current_user.is_authenticated:
        if current_user.is_admin:
            return url_for('admin.dashboard')  # adjust blueprint/route name as needed
        else:
            return url_for('bookings.dashboard')
    return url_for('main.index')  # fallback

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(get_user_dashboard_url())

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))

        # Log the user in
        login_user(user, remember=form.remember_me.data)

        # Redirect based on role
        flash('Login successful!', 'success')
        return redirect(get_user_dashboard_url())

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration + auto-login after success"""
    if current_user.is_authenticated:
        return redirect(get_user_dashboard_url())

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # Automatically log the new user in
        login_user(user)

        flash('Registration successful! Welcome to Eni\'s Apartments.', 'success')
        return redirect(get_user_dashboard_url())

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page and updates"""
    if request.method == 'POST':
        data = request.get_json()
        
        current_user.first_name = data.get('first_name', current_user.first_name)
        current_user.last_name = data.get('last_name', current_user.last_name)
        current_user.phone = data.get('phone', current_user.phone)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})
