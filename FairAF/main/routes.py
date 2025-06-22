from flask import Blueprint, render_template, send_file, current_app, flash, redirect, url_for, request
from flask_login import login_required, current_user
from io import BytesIO
from ..models import db, User, Chore, Expense, ExpenseShare, Penalty, Group
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    # Only show members of the current user's group!
    if not current_user.group_id:
        flash("You are not in a group. Please join or create one.", "warning")
        return redirect(url_for('main.group_settings'))

    members = User.query.filter_by(group_id=current_user.group_id).all()
    chores = Chore.query.filter(Chore.assigned_to_id.in_([u.id for u in members])).order_by(Chore.due_date).all()
    expenses = Expense.query.filter(Expense.created_by_id.in_([u.id for u in members])).order_by(Expense.created_at.desc()).all()
    penalties = Penalty.query.filter(Penalty.user_id.in_([u.id for u in members])).order_by(Penalty.applied_at.desc()).all()

    user_balances = {}
    for user in members:
        paid = sum(s.amount for s in user.expense_shares)
        user_balances[user.username] = paid

    next_chore = (
        Chore.query.filter_by(assigned_to_id=current_user.id, completed=False)
        .order_by(Chore.due_date)
        .first()
    )
    my_penalties = Penalty.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "dashboard.html",
        chores=chores,
        expenses=expenses,
        next_chore=next_chore,
        user_balances=user_balances,
        penalties=penalties,
        my_penalties=my_penalties,
        users=members  # Only members of my group!
    )

@main_bp.route('/export/pdf')
@login_required
def export_pdf():
    if not current_user.group_id:
        flash("You are not in a group. Please join or create one.", "warning")
        return redirect(url_for('main.group_settings'))

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "FairAF Roommate Dashboard Summary")
    y -= 30
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Exported on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Chores:")
    y -= 20

    members = User.query.filter_by(group_id=current_user.group_id).all()
    member_ids = [u.id for u in members]
    for chore in Chore.query.filter(Chore.assigned_to_id.in_(member_ids)).order_by(Chore.due_date).all():
        s = f"{chore.title} - Due: {chore.due_date.strftime('%Y-%m-%d') if chore.due_date else 'N/A'}, Assigned: {chore.user.username if chore.user else '-'}, Completed: {'Yes' if chore.completed else 'No'}"
        p.drawString(60, y, s)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Expenses:")
    y -= 20
    for exp in Expense.query.filter(Expense.created_by_id.in_(member_ids)).order_by(Expense.created_at.desc()).all():
        s = f"{exp.title}: ${exp.total_amount:.2f}, By: {exp.created_by_id}, Date: {exp.created_at.strftime('%Y-%m-%d')}"
        p.drawString(60, y, s)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Penalties:")
    y -= 20
    for pen in Penalty.query.filter(Penalty.user_id.in_(member_ids)).order_by(Penalty.applied_at.desc()).all():
        u = User.query.get(pen.user_id)
        s = f"{u.username if u else '-'} - Amount: ${pen.amount:.2f} on {pen.applied_at.strftime('%Y-%m-%d')}"
        p.drawString(60, y, s)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='FairAF_dashboard.pdf', mimetype='application/pdf')

# ---------------------- GROUP FEATURES ----------------------

@main_bp.route('/group/settings', methods=['GET', 'POST'])
@login_required
def group_settings():
    group = current_user.group
    if not group:
        flash("You are not in a group. Please join or create one.", "warning")
        return redirect(url_for('main.dashboard'))

    members = User.query.filter_by(group_id=group.id).all()
    if request.method == "POST":
        group.name = request.form.get('group_name', group.name)
        db.session.commit()
        flash("Group name updated.", "success")
        return redirect(url_for('main.group_settings'))
    return render_template('group.html', group=group, members=members)

@main_bp.route('/group/join', methods=['GET', 'POST'])
@login_required
def join_group():
    if request.method == 'POST':
        code = request.form['group_code'].strip().upper()
        group = Group.query.filter_by(code=code).first()
        if group:
            current_user.group_id = group.id
            db.session.commit()
            flash(f"Joined group {group.name}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid group code.", "danger")
    return render_template('join_group.html')

@main_bp.route('/group/leave', methods=['POST'])
@login_required
def leave_group():
    current_user.group_id = None
    db.session.commit()
    flash("You have left the group.", "info")
    return redirect(url_for('main.dashboard'))

@main_bp.route('/group/kick/<int:user_id>', methods=['POST'])
@login_required
def kick_member(user_id):
    if not current_user.is_admin or current_user.id == user_id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.group_settings'))
    user = User.query.get_or_404(user_id)
    if user.group_id == current_user.group_id:
        user.group_id = None
        db.session.commit()
        flash(f"{user.username} has been removed from the group.", "info")
    else:
        flash("User not in your group.", "danger")
    return redirect(url_for('main.group_settings'))
