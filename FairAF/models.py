from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import random
import string

db = SQLAlchemy()

def generate_unique_group_code(length=6):
    """Generate a unique group code every time."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Group.query.filter_by(code=code).first():
            return code

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default="My Roommate Group")
    code = db.Column(db.String(16), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    group = db.relationship('Group', backref='members')

    chores = db.relationship('Chore', backref='user', lazy=True)
    expense_shares = db.relationship('ExpenseShare', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    proof_image = db.Column(db.String(256))
    shares = db.relationship('ExpenseShare', backref='expense', lazy=True)

class ExpenseShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    due_date = db.Column(db.DateTime)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    proof_image = db.Column(db.String(256))
    penalty_applied = db.Column(db.Boolean, default=False)
    penalty_amount = db.Column(db.Float, default=0.0)

class Penalty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
