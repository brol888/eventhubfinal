from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField
from wtforms.fields import DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    short_description = StringField("Short Description", validators=[DataRequired(), Length(max=300)])
    full_description = TextAreaField("Full Description", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    event_date = DateTimeField("Event Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    ticket_price = FloatField("Ticket Price", validators=[DataRequired(), NumberRange(min=0)])
    organizer = StringField("Organizer", validators=[DataRequired()])
    category = SelectField(
        "Category",
        choices=[
            ("Music", "Music"),
            ("Tech", "Tech"),
            ("Art", "Art"),
            ("Sport", "Sport"),
            ("Education", "Education"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Post Event")



class EditProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField("Profile Picture", validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")])
    submit = SubmitField("Save Changes")