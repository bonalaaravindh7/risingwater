from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, FloatField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, ValidationError

from models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with that email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me signed in")
    submit = SubmitField("Log in")


class PredictForm(FlaskForm):
    """Mirrors the original request.form fields, but validated server-side."""

    Temp = FloatField("Temperature (°C)", validators=[DataRequired(), NumberRange(-50, 60)])
    Humidity = FloatField("Humidity (%)", validators=[DataRequired(), NumberRange(0, 100)])
    CloudCover = FloatField("Cloud Cover (%)", validators=[DataRequired(), NumberRange(0, 100)])
    Annual = FloatField("Annual Rain Fall (mm)", validators=[DataRequired(), NumberRange(0, 20000)])
    JanFeb = FloatField("Jan-Feb Rainfall (mm)", validators=[DataRequired(), NumberRange(0, 10000)])
    MarMay = FloatField("March-May Rainfall (mm)", validators=[DataRequired(), NumberRange(0, 10000)])
    JunSep = FloatField("June-September Rainfall (mm)", validators=[DataRequired(), NumberRange(0, 15000)])
    OctDec = FloatField("Oct-Dec Rainfall (mm)", validators=[DataRequired(), NumberRange(0, 10000)])
    AvgJune = FloatField("Average June Rainfall (mm)", validators=[DataRequired(), NumberRange(0, 5000)])
    Sub = FloatField("Sub-division Rainfall (mm)", validators=[DataRequired(), NumberRange(0, 20000)])
    submit = SubmitField("Predict")
