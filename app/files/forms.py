from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField
from flask_wtf.file import FileField, FileRequired


class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[FileRequired(message="Please choose a file.")])

    # Recipients are OPTIONAL now. If empty => only owner has access.
    recipients = SelectMultipleField(
        "Authorized Recipients",
        coerce=int,  # we use user IDs as integers
    )

    submit = SubmitField("Upload Encrypted File")
