from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import db, Group, Fund, User, Penalty

group_fund_bp = Blueprint('group_fund', __name__)

@group_fund_bp.route('/group', methods=['GET', 'POST'])
@login_required
def group_settings():
    group = Group.query.first()
    if not group:
        group = Group(name="My Roommate Group")
        db.session.add(group)
        db.session.commit()
    if request.method == 'POST':
        group.name = request.form['group_name']
        db.session.commit()
        flash("Group name updated!", "success")
        return redirect(url_for('group_fund.group_settings'))
    members = User.query.all()
    return render_template('group.html', group=group, members=members)

@group_fund_bp.route('/fund')
@login_required
def fund_page():
    fund = Fund.query.first()
    if not fund:
        fund = Fund(total=0.0)
        db.session.add(fund)
        db.session.commit()
    penalties = Penalty.query.all()
    total_penalties = sum(p.amount for p in penalties)
    fund.total = total_penalties
    db.session.commit()
    penalty_by_user = {}
    for p in penalties:
        penalty_by_user.setdefault(p.user_id, 0)
        penalty_by_user[p.user_id] += p.amount
    members = User.query.all()
    return render_template('fund.html', fund=fund, penalties=penalties, penalty_by_user=penalty_by_user, members=members)
