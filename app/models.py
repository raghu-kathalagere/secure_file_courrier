from datetime import datetime
from .extensions import db, login_manager
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    public_key = db.Column(db.Text, nullable=False)   # PEM format
    private_key = db.Column(db.Text, nullable=False)  # PEM format (plain or encrypted)

    # Team / group name for isolation (only same team visible as recipients)
    team_name = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owned_files = db.relationship("File", backref="owner", lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    filename = db.Column(db.String(255), nullable=False)     # original filename
    stored_path = db.Column(db.String(500), nullable=False)  # path in /data
    revoked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    keys = db.relationship("FileKey", backref="file", lazy=True, cascade="all, delete-orphan")
    events = db.relationship("FileEvent", backref="file", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<File {self.filename} (id={self.id})>"


class FileKey(db.Model):
    __tablename__ = "file_keys"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    encrypted_file_key = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("file_keys", lazy=True))

    def __repr__(self):
        return f"<FileKey file={self.file_id} user={self.user_id}>"


class FileEvent(db.Model):
    __tablename__ = "file_events"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    action = db.Column(db.String(50), nullable=False)  # UPLOAD, DOWNLOAD, REVOKE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("events", lazy=True))

    def __repr__(self):
        return f"<FileEvent file={self.file_id} user={self.user_id} action={self.action}>"


# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
