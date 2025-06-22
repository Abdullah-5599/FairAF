import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from FairAF import create_app   # Change 'FairAF' to your app name if needed
from FairAF.models import db, User, Group

app = create_app()
with app.app_context():
    # Delete all users
    user_count = User.query.delete()
    # Delete all groups
    group_count = Group.query.delete()
    db.session.commit()
    print(f"Deleted {user_count} users and {group_count} groups.")

