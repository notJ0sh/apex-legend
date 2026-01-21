# STORE UR CLASSES HERE

from flask_login import UserMixin

# User class


class User(UserMixin):
    def __init__(self, id, username, user_role, department=None):
        self.id = id
        self.username = username
        self.role = user_role
        self.department = department


# File class
class File:
    def __init__(self, id, file_name, file_type, file_path, department,
                 time_stamp=None, user=None, project=None, source=None):
        self.id = id
        self.file_name = file_name
        self.file_type = file_type
        self.file_path = file_path
        self.department = department
        self.time_stamp = time_stamp
        self.user = user
        self.project = project
        self.source = source

    @classmethod
    def from_row(cls, row):
        """Factory method to create a File object from a sqlite3.Row."""
        return cls(
            id=row['id'],
            file_name=row['file_name'],
            file_type=row['file_type'],
            file_path=row['file_path'],
            department=row['department'],
            time_stamp=row['time_stamp'],
            user=row['user'],
            project=row['project'],
            source=row['source']
        )

    def to_dict(self):
        """Helper to convert the object back to a dict (useful for JSON responses)."""
        return self.__dict__
