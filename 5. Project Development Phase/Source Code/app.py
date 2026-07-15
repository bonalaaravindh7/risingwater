import os
import logging

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
import joblib
import pandas as pd

from extensions import db, login_manager, csrf
from models import User, Prediction
from forms import RegistrationForm, LoginForm, PredictForm

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Render/Heroku/most PaaS hosts terminate HTTPS at a proxy and forward plain
# HTTP internally. Without this, url_for(..., _external=True) — used to
# build the Google OAuth callback URL — would generate http:// instead of
# https://, which Google rejects as a redirect_uri mismatch.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///floods.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Only send cookies over HTTPS once you're live behind TLS. Keep this off for
# local http://127.0.0.1 testing — set SESSION_COOKIE_SECURE=true in your
# production host's environment variables once deployed.
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# Google OAuth ("Continue with Google") — only registered if credentials are
# present, so the app still runs fine without them (the button just won't
# be wired to anything functional).
# ---------------------------------------------------------------------------
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_LOGIN_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

oauth = OAuth(app)
if GOOGLE_LOGIN_ENABLED:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
else:
    logger.warning("GOOGLE_CLIENT_ID/SECRET not set — 'Continue with Google' is disabled.")

# ---------------------------------------------------------------------------
# ML model / scaler — loaded once at startup. If either file is missing or
# corrupt we keep the app running (so auth/history pages still work) but
# disable the /predict endpoint instead of crashing the whole process.
# ---------------------------------------------------------------------------
MODEL_READY = True
try:
    model = joblib.load("floods.save")
    scaler = joblib.load("transform.save")
except Exception:
    logger.exception("Failed to load model/scaler — prediction will be unavailable.")
    model = None
    scaler = None
    MODEL_READY = False

FEATURE_COLUMNS = [
    "Temp",
    "Humidity",
    "Cloud Cover",
    "ANNUAL",
    "Jan-Feb",
    "Mar-May",
    "Jun-Sep",
    "Oct-Dec",
    "avgjune",
    "sub",
]


@app.context_processor
def inject_google_login_flag():
    return {"google_login_enabled": GOOGLE_LOGIN_ENABLED}


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created — welcome!", "success")
        return redirect(url_for("home"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Incorrect email or password.", "error")
        else:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.username}.", "success")
            next_page = request.args.get("next")
            # Only follow local, relative redirect targets to avoid open-redirect abuse.
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("home"))

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("home"))


def _unique_username_from_email(email):
    """Turn an email's local part into a free username, adding a numeric
    suffix if it's already taken (e.g. 'lahari' -> 'lahari2')."""
    base = email.split("@")[0].strip() or "user"
    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first() is not None:
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


@app.route("/login/google")
def login_google():
    if not GOOGLE_LOGIN_ENABLED:
        flash("Google sign-in isn't configured on this server yet.", "error")
        return redirect(url_for("login"))
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/login/google/callback")
def google_callback():
    if not GOOGLE_LOGIN_ENABLED:
        flash("Google sign-in isn't configured on this server yet.", "error")
        return redirect(url_for("login"))

    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or oauth.google.userinfo()
    except Exception:
        logger.exception("Google OAuth callback failed")
        flash("Google sign-in didn't complete. Please try again.", "error")
        return redirect(url_for("login"))

    google_id = userinfo.get("sub")
    email = (userinfo.get("email") or "").strip().lower()

    if not google_id or not email:
        flash("Google didn't share the info we need to sign you in.", "error")
        return redirect(url_for("login"))

    # Match an existing account by google_id first, then by email (so a user
    # who originally signed up with a password can still link Google).
    user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        user = User.query.filter_by(email=email).first()
        if user is not None:
            user.google_id = google_id
        else:
            user = User(
                username=_unique_username_from_email(email),
                email=email,
                google_id=google_id,
            )
            db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(f"Welcome, {user.username}.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if not MODEL_READY:
        flash("The prediction model is currently unavailable. Please try again later.", "error")
        return render_template("predict.html", form=PredictForm(), model_ready=False)

    form = PredictForm()

    if form.validate_on_submit():
        try:
            data = pd.DataFrame(
                [[
                    form.Temp.data,
                    form.Humidity.data,
                    form.CloudCover.data,
                    form.Annual.data,
                    form.JanFeb.data,
                    form.MarMay.data,
                    form.JunSep.data,
                    form.OctDec.data,
                    form.AvgJune.data,
                    form.Sub.data,
                ]],
                columns=FEATURE_COLUMNS,
            )

            scaled = scaler.transform(data)
            prediction = model.predict(scaled)
            flood_predicted = bool(prediction[0] == 1)

            record = Prediction(
                user_id=current_user.id,
                temp=form.Temp.data,
                humidity=form.Humidity.data,
                cloud_cover=form.CloudCover.data,
                annual=form.Annual.data,
                jan_feb=form.JanFeb.data,
                mar_may=form.MarMay.data,
                jun_sep=form.JunSep.data,
                oct_dec=form.OctDec.data,
                avg_june=form.AvgJune.data,
                sub=form.Sub.data,
                flood_predicted=flood_predicted,
            )
            db.session.add(record)
            db.session.commit()

            return render_template("chance.html" if flood_predicted else "no_chance.html")

        except Exception:
            logger.exception("Prediction failed")
            flash("Something went wrong while generating the prediction. Please check your inputs and try again.", "error")

    return render_template("predict.html", form=form, model_ready=True)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
@app.route("/history")
@login_required
def history():
    predictions = current_user.predictions.all()
    return render_template("history.html", predictions=predictions)


@app.route("/history/<int:prediction_id>/delete", methods=["POST"])
@login_required
def delete_prediction(prediction_id):
    record = db.session.get(Prediction, prediction_id)
    if record is None or record.user_id != current_user.id:
        abort(404)
    db.session.delete(record)
    db.session.commit()
    flash("Prediction removed from your history.", "info")
    return redirect(url_for("history"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(_error):
    db.session.rollback()
    return render_template("errors/500.html"), 500


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
