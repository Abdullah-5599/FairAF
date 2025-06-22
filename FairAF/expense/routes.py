from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from ..models import db, Expense, ExpenseShare, User

expense_bp = Blueprint('expense', __name__, url_prefix='/expenses')

@expense_bp.route('/', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        total_amount = float(request.form['total_amount'])
        shares_data = request.form.getlist('share_amount')
        user_ids = request.form.getlist('user_id')
        proof_image_file = request.files.get('proof_image')

        proof_image_filename = None
        if proof_image_file and proof_image_file.filename:
            uploads_folder = os.path.join(current_app.static_folder, "uploads")
            os.makedirs(uploads_folder, exist_ok=True)
            proof_image_filename = secure_filename(proof_image_file.filename)
            proof_image_file.save(os.path.join(uploads_folder, proof_image_filename))

        expense = Expense(
            title=title,
            description=description,
            total_amount=total_amount,
            created_by_id=current_user.id,
            proof_image=proof_image_filename
        )
        db.session.add(expense)
        db.session.commit()

        for uid, amount in zip(user_ids, shares_data):
            db.session.add(ExpenseShare(
                expense_id=expense.id,
                user_id=int(uid),
                amount=float(amount)
            ))
        db.session.commit()
        flash("Expense added with custom split!", "success")
        return redirect(url_for('expense.expenses'))

    expenses = Expense.query.order_by(Expense.created_at.desc()).all()
    users = User.query.all()
    return render_template('expenses.html', expenses=expenses, users=users)

@expense_bp.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    # Optional: add admin/owner check
    ExpenseShare.query.filter_by(expense_id=expense_id).delete()
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'info')
    return redirect(url_for('expense.expenses'))
