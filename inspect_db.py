from FairAF import create_app, db
from FairAF.models import Group, User

app = create_app()  # Make sure this matches your app factory function

with app.app_context():
    users = User.query.all()
    groups = Group.query.all()

    print("Groups:")
    for g in groups:
        print(f"ID: {g.id}, Code: {g.code}, Name: {g.name}")

    print("\nUsers:")
    for u in users:
        print(f"Username: {u.username}, Group ID: {u.group_id}, Is Admin: {u.is_admin}")
