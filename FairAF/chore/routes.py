from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..models import db, Chore, Penalty, User
import os
from datetime import datetime, timedelta

chore_bp = Blueprint('chore', __name__, url_prefix='/chores')

@chore_bp.route('/', methods=['GET', 'POST'])
@login_required
def chores():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        assigned_to_id = request.form['assigned_to']
        penalty_amount = float(request.form.get('penalty_amount', 0))  # NEW: get from form!
        proof_image_file = request.files.get('proof_image')

        proof_image_filename = None
        if proof_image_file and proof_image_file.filename:
            uploads_folder = os.path.join(current_app.static_folder, "uploads")
            os.makedirs(uploads_folder, exist_ok=True)
            proof_image_filename = secure_filename(proof_image_file.filename)
            proof_image_file.save(os.path.join(uploads_folder, proof_image_filename))

        chore = Chore(
            title=title,
            description=description,
            due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            assigned_to_id=int(assigned_to_id),
            proof_image=proof_image_filename,
            penalty_amount=penalty_amount  # NEW: store the custom penalty!
        )
        db.session.add(chore)
        db.session.commit()
        flash("Chore created!", "success")
        return redirect(url_for('chore.chores'))

    # Penalty logic: apply if incomplete after due date
    now = datetime.utcnow()
    chores = Chore.query.order_by(Chore.due_date).all()
    for chore in chores:
        if (chore.due_date and chore.due_date < now and not chore.completed and not chore.penalty_applied):
            penalty_amount = chore.penalty_amount or 5.0  # Use chore's set penalty!
            penalty = Penalty(chore_id=chore.id, user_id=chore.assigned_to_id, amount=penalty_amount)
            db.session.add(penalty)
            chore.penalty_applied = True
            chore.penalty_amount = penalty_amount
            db.session.commit()
            flash(f"Penalty of ${penalty_amount:.2f} applied for missed chore: {chore.title}", "warning")
    users = User.query.all()
    return render_template('chores.html', chores=chores, users=users)

@chore_bp.route('/complete/<int:chore_id>', methods=['POST'])
@login_required
def complete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    if current_user.id != chore.assigned_to_id and not current_user.is_admin:
        flash("Not authorized.", "danger")
        return redirect(url_for('chore.chores'))
    chore.completed = True
    chore.completed_at = datetime.utcnow()
    db.session.commit()
    flash("Chore marked as completed!", "success")
    return redirect(url_for('chore.chores'))

@chore_bp.route('/delete/<int:chore_id>', methods=['POST'])
@login_required
def delete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    if current_user.id != chore.assigned_to_id and not current_user.is_admin:
        flash("Not authorized.", "danger")
        return redirect(url_for('chore.chores'))
    Penalty.query.filter_by(chore_id=chore.id).delete()
    db.session.delete(chore)
    db.session.commit()
    flash('Chore deleted.', 'info')
    return redirect(url_for('chore.chores'))
