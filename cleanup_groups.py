import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from FairAF import create_app   # <-- change 'FairAF' to your actual app package name if needed
from FairAF.models import db, Group, User

app = create_app()
with app.app_context():
    # Step 1: Find all bad groups (code is None or '')
    bad_groups = Group.query.filter((Group.code == None) | (Group.code == '')).all()
    bad_group_ids = [g.id for g in bad_groups]

    # Step 2: Optionally, delete users assigned to those groups
    users_deleted = User.query.filter(User.group_id.in_(bad_group_ids)).delete(synchronize_session=False)
    
    # Step 3: Delete the groups
    groups_deleted = Group.query.filter((Group.code == None) | (Group.code == '')).delete(synchronize_session=False)

    db.session.commit()
    print(f"Deleted {groups_deleted} bad groups and {users_deleted} users assigned to them.")
