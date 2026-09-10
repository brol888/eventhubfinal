from flask import Flask, render_template, redirect, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Event
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import logging
import os
from werkzeug.utils import secure_filename
from forms import RegisterForm, LoginForm, EventForm, EditProfileForm
import requests

app = Flask(__name__)

logging.basicConfig(
    filename="eventhub.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

app.config["SECRET_KEY"] = "dev-secret-key-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventhub.db"
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def get_weather(location):
    try:
        # Step 1: turn the location name into latitude/longitude
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_response = requests.get(geo_url, params={"name": location, "count": 1}, timeout=5)
        geo_data = geo_response.json()

        if "results" not in geo_data or len(geo_data["results"]) == 0:
            logging.info(f"API request error: {location}")
            return None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # Step 2: get current weather for those coordinates
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_response = requests.get(
            weather_url,
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=5
        )
        weather_data = weather_response.json()

        current = weather_data["current_weather"]
        return {
            "temp": current["temperature"],
            "windspeed": current["windspeed"]
        }

    except requests.exceptions.RequestException:
        logging.info(f"API request error: {location}")
        return None

@app.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.user_id != current_user.id:
        abort(403)

    form = EventForm(obj=event)

    if form.validate_on_submit():
        event.title = form.title.data
        event.short_description = form.short_description.data
        event.full_description = form.full_description.data
        event.location = form.location.data
        event.event_date = form.event_date.data
        event.ticket_price = form.ticket_price.data
        event.organizer = form.organizer.data
        event.category = form.category.data

        db.session.commit()

        logging.info(f"Event edited: {event.title}")
        flash("Event updated successfully.")
        return redirect(url_for("event_detail", event_id=event.id))

    return render_template("edit_event.html", form=form, event=event)


@app.route("/event/<int:event_id>/delete")
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.user_id != current_user.id:
        abort(403)

    db.session.delete(event)
    db.session.commit()

    logging.info(f"Event deleted: {event.title}")
    flash("Event deleted.")
    return redirect(url_for("home"))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("index.html", events=events)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created. You can now log in.")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            logging.info(f"Successful login: {user.email}")
            return redirect(url_for("home"))
        else:
            logging.info(f"Failed login: {form.email.data}")
            flash("Invalid email or password.")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logging.info(f"Logout: {current_user.email}")
    logout_user()
    return redirect(url_for("home"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/add-event", methods=["GET", "POST"])
@login_required
def add_event():
    form = EventForm()

    if form.validate_on_submit():
        new_event = Event(
            title=form.title.data,
            short_description=form.short_description.data,
            full_description=form.full_description.data,
            location=form.location.data,
            event_date=form.event_date.data,
            ticket_price=form.ticket_price.data,
            organizer=form.organizer.data,
            category=form.category.data,
            user_id=current_user.id
        )
        db.session.add(new_event)
        db.session.commit()

        logging.info(f"Event added: {new_event.title}")
        flash("Event posted successfully.")
        return redirect(url_for("home"))

    return render_template("add_event.html", form=form)

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data

        if form.picture.data:
            filename = secure_filename(form.picture.data.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            form.picture.data.save(filepath)
            current_user.profile_image = filename

        db.session.commit()
        flash("Profile updated.")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", form=form)

@app.route("/event/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    weather = get_weather(event.location)
    return render_template("event_detail.html", event=event, weather=weather)

@app.route("/user/<int:user_id>/events")
def user_events(user_id):
    return f"Events by user {user_id} coming soon"


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)


