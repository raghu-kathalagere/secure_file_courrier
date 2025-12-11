from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
    send_file,
    jsonify,
)
from flask_login import login_required, current_user
from ..extensions import db
from ..models import User, File, FileKey, FileEvent
from .forms import UploadFileForm
from ..crypto_utils import (
    generate_aes_key,
    aes_gcm_encrypt_to_blob,
    aes_gcm_decrypt_from_blob,
    encrypt_file_key_for_user,
    decrypt_file_key_for_user,
)
from ..storage_utils import save_encrypted_file, load_encrypted_file, delete_file_if_exists

files_bp = Blueprint("files", __name__)


# ---------- Helper ----------

def log_event(file_id: int, user_id: int, action: str):
    event = FileEvent(file_id=file_id, user_id=user_id, action=action)
    db.session.add(event)


# ---------- HTML VIEWS ----------

@files_bp.route("/")
@login_required
def dashboard():
    """
    Dashboard:
    - Files you own
    - Files shared with you
    """
    # Files owned by current user
    owned_files = File.query.filter_by(owner_id=current_user.id).all()

    # Files shared with current user via FileKey (but not revoked)
    shared_keys = FileKey.query.filter_by(user_id=current_user.id).all()
    shared_file_ids = {fk.file_id for fk in shared_keys}
    shared_files = []
    if shared_file_ids:
        shared_files = (
            File.query.filter(File.id.in_(shared_file_ids), File.revoked == False)
            .all()
        )

    return render_template(
        "files/dashboard.html",
        owned_files=owned_files,
        shared_files=shared_files,
    )


@files_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """
    Encrypted file upload:
    - Choose file
    - (Optionally) select recipients (only same team)
    - Generate AES-256 key
    - Encrypt file with AES-GCM (nonce|tag|ciphertext)
    - Encrypt file key per recipient using RSA
    - Store metadata + log UPLOAD
    """
    form = UploadFileForm()

    # Populate recipient choices with users in the SAME TEAM only (and not self)
    if current_user.team_name:
        users = User.query.filter(
            User.id != current_user.id,
            User.team_name == current_user.team_name,
        ).all()
    else:
        users = []

    form.recipients.choices = [(u.id, u.email) for u in users]

    if form.validate_on_submit():
        file_storage = form.file.data    # Werkzeug FileStorage
        recipients_ids = form.recipients.data or []  # list of user IDs (int)

        # Read file bytes
        original_filename = file_storage.filename
        file_bytes = file_storage.read()

        # 100MB limit also enforced at app level via MAX_CONTENT_LENGTH, but double-check:
        if len(file_bytes) > 100 * 1024 * 1024:
            flash("File too large (max 100MB).", "danger")
            return redirect(url_for("files.upload"))

        # Generate AES-256 key and encrypt file
        aes_key = generate_aes_key()
        encrypted_blob = aes_gcm_encrypt_to_blob(file_bytes, aes_key)

        # Save encrypted file
        stored_path = save_encrypted_file(original_filename, encrypted_blob)

        # Create File record
        new_file = File(
            owner_id=current_user.id,
            filename=original_filename,
            stored_path=stored_path,
            revoked=False,
        )
        db.session.add(new_file)
        db.session.flush()  # get new_file.id before commit

        # Ensure owner can always access
        unique_recipient_ids = set(recipients_ids)
        unique_recipient_ids.add(current_user.id)

        # Validate and encrypt AES key for each authorized user
        for uid in unique_recipient_ids:
            user = User.query.get(uid)
            if not user:
                # If any invalid user ID is present, rollback
                db.session.rollback()
                delete_file_if_exists(stored_path)
                flash("Invalid recipient selected.", "danger")
                return redirect(url_for("files.upload"))

            encrypted_file_key = encrypt_file_key_for_user(aes_key, user.public_key)
            fk = FileKey(
                file_id=new_file.id,
                user_id=user.id,
                encrypted_file_key=encrypted_file_key,
            )
            db.session.add(fk)

        # Log UPLOAD event
        log_event(file_id=new_file.id, user_id=current_user.id, action="UPLOAD")

        db.session.commit()
        flash("File uploaded and encrypted successfully.", "success")
        return redirect(url_for("files.dashboard"))

    return render_template("files/upload.html", form=form)


@files_bp.route("/files/<int:file_id>/download")
@login_required
def download(file_id):
    """
    Secure download:
    - Check user is authorized (FileKey exists)
    - Check file not revoked
    - Decrypt AES key using user's private RSA key
    - Decrypt file with AES-GCM
    - Send plaintext file for download
    """
    file_obj = File.query.get_or_404(file_id)

    if file_obj.revoked:
        flash("This file has been revoked by the owner.", "danger")
        return redirect(url_for("files.dashboard"))

    # Check user has an encrypted file key for this file
    file_key_entry = FileKey.query.filter_by(file_id=file_id, user_id=current_user.id).first()
    if not file_key_entry:
        abort(403)  # forbidden

    # Decrypt AES key with user's private RSA key
    try:
        aes_key = decrypt_file_key_for_user(
            file_key_entry.encrypted_file_key,
            current_user.private_key,
        )
    except Exception:
        flash("Failed to decrypt file key. Access denied.", "danger")
        return redirect(url_for("files.dashboard"))

    # Load encrypted blob and decrypt file content
    encrypted_blob = load_encrypted_file(file_obj.stored_path)
    try:
        plaintext = aes_gcm_decrypt_from_blob(encrypted_blob, aes_key)
    except Exception:
        flash("Decryption failed or file corrupted.", "danger")
        return redirect(url_for("files.dashboard"))

    # Log DOWNLOAD event
    log_event(file_id=file_obj.id, user_id=current_user.id, action="DOWNLOAD")
    db.session.commit()

    # Serve file as attachment (no temp file left on disk)
    return send_file(
        BytesIO(plaintext),
        as_attachment=True,
        download_name=file_obj.filename,
        mimetype="application/octet-stream",
    )


@files_bp.route("/files/<int:file_id>/revoke", methods=["POST"])
@login_required
def revoke(file_id):
    """
    Owner-only revoke:
    - Mark file as revoked
    - Delete encrypted data from disk
    - Remove file keys from DB
    - Log REVOKE event
    """
    file_obj = File.query.get_or_404(file_id)

    if file_obj.owner_id != current_user.id:
        abort(403)

    if file_obj.revoked:
        flash("File is already revoked.", "info")
        return redirect(url_for("files.dashboard"))

    # Mark revoked
    file_obj.revoked = True

    # Delete physical encrypted file
    delete_file_if_exists(file_obj.stored_path)
    file_obj.stored_path = ""

    # Delete all file keys
    FileKey.query.filter_by(file_id=file_obj.id).delete()

    # Log REVOKE event
    log_event(file_id=file_obj.id, user_id=current_user.id, action="REVOKE")

    db.session.commit()
    flash("File access revoked and encryption keys wiped.", "warning")
    return redirect(url_for("files.dashboard"))


@files_bp.route("/files/<int:file_id>/logs")
@login_required
def logs(file_id):
    """
    Show access logs (UPLOAD, DOWNLOAD, REVOKE) for owner.
    """
    file_obj = File.query.get_or_404(file_id)
    if file_obj.owner_id != current_user.id:
        abort(403)

    events = (
        FileEvent.query.filter_by(file_id=file_id)
        .order_by(FileEvent.created_at.desc())
        .all()
    )

    return render_template("files/logs.html", file=file_obj, events=events)


@files_bp.route("/files/<int:file_id>")
@login_required
def file_detail(file_id):
    """
    Detailed view:
    - Owner: can see recipients, logs link, revoke, download
    - Recipient: can download only
    """
    file_obj = File.query.get_or_404(file_id)

    is_owner = (file_obj.owner_id == current_user.id)

    has_access = (
        FileKey.query.filter_by(file_id=file_id, user_id=current_user.id).first()
        is not None
    )

    if not (is_owner or has_access):
        abort(403)

    authorized_keys = FileKey.query.filter_by(file_id=file_id).all()
    recipients = [fk.user for fk in authorized_keys] if is_owner else None

    return render_template(
        "files/file_detail.html",
        file=file_obj,
        is_owner=is_owner,
        recipients=recipients,
    )


# ---------- JSON API ----------

@files_bp.route("/api/files", methods=["GET"])
@login_required
def api_list_files():
    owned_files = File.query.filter_by(owner_id=current_user.id).all()
    shared_keys = FileKey.query.filter_by(user_id=current_user.id).all()
    shared_file_ids = {fk.file_id for fk in shared_keys}
    shared_files = []
    if shared_file_ids:
        shared_files = (
            File.query.filter(File.id.in_(shared_file_ids), File.revoked == False)
            .all()
        )

    def serialize_file(f: File, role: str):
        return {
            "id": f.id,
            "filename": f.filename,
            "owner_id": f.owner_id,
            "revoked": f.revoked,
            "role": role,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }

    data = {
        "owned": [serialize_file(f, "owner") for f in owned_files],
        "shared": [serialize_file(f, "recipient") for f in shared_files],
    }
    return jsonify(data)


@files_bp.route("/api/files/<int:file_id>/logs", methods=["GET"])
@login_required
def api_logs(file_id):
    file_obj = File.query.get_or_404(file_id)
    if file_obj.owner_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    events = (
        FileEvent.query.filter_by(file_id=file_id)
        .order_by(FileEvent.created_at.desc())
        .all()
    )

    data = []
    for e in events:
        data.append(
            {
                "id": e.id,
                "user_id": e.user_id,
                "user_email": e.user.email if e.user else None,
                "action": e.action,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
        )
    return jsonify(data)
