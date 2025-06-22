from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User, Group, generate_unique_group_code

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form

        # Check for existing user/email
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.signup'))

        if is_admin:
            # Always create a new group with unique code
            code = generate_unique_group_code()
            group = Group(name=f"{username}'s Group", code=code)
            db.session.add(group)
            db.session.commit()  # Assign group.id

            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                is_admin=True,
                group_id=group.id
            )
            db.session.add(user)
            db.session.commit()
            flash(f'Account created! Your group code is {code}. Please log in.', 'success')
        else:
            # Non-admin: must join via group code
            group_code = request.form.get('group_code', '').strip().upper()
            group = Group.query.filter_by(code=group_code).first()
            if not group:
                flash('Invalid group code. Please get a code from your roommate or admin.', 'danger')
                return redirect(url_for('auth.signup'))

            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                is_admin=False,
                group_id=group.id
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')

        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
