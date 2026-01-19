# STORE UR CLASSES HERE

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, user_role, department=None):
        self.id = id
        self.username = username
        self.role = user_role
        self.department = department
