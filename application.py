import os
import csv
import json

from flask import Flask, session, request, flash, jsonify, redirect, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import password_check, login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set caching of CSS and JS files to 0
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    return "Project 1: TODO"
    ## return render_termplate("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please enter username")
            return render_template("register.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please enter password")
            return render_template("register.html")

        # Check if password fulfils requirements for valid password
        elif not password_check(request.form.get("password")):
            flash("Passwords should be at least eight and at most 30 characters long, contain one uppercase and one lowercase letter and one of the symbols $@#%&_")
            return render_template("register.html")

        # Ensure second entry of password matches first
        elif not request.form.get("confirmation") == request.form.get("password"):
            flash("Passwords must match")
            return render_template("register.html")
        else:
            username = request.form.get("username")
            password = request.form.get("password")

        # Query database for username to check it doesn't exist already
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": username}).fetchone()
        print(rows)

        if rows is not None:
            flash("Username already exists")
            return render_template("register.html")

        # Insert username and password hash into database
        db.execute("INSERT INTO users(username, pw_hash) VALUES (:username, :pw_hash)",
                   {"username": username, "pw_hash": generate_password_hash(password)})

        # Retrieve the id from the user
        id = db.execute("SELECT user_id FROM users WHERE username = :username",
                        {"username": username}).fetchone()
        print(id)

        # Remember the id of the user who has just registered
        session["user_id"] = id
        print(session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please enter username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please enter password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        # Ensure username exists and password is correct
        if rows is None:
            flash("Invalid username")
        else:
            if not check_password_hash(rows["pw_hash"], request.form.get("password")):
                flash("Invalid password")
        return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/search")
@login_required
def search():
    return "Search: TODO"


@app.route("/confirm", methods=["POST"])
@login_required
def book():
    """Confirm selection."""
    ## TODO

    # Get form information.
    name = request.form.get("name")
    try:
        flight_id = int(request.form.get("flight_id"))
    except ValueError:
        return render_template("error.html", message="Invalid flight number.")

    # Make sure the flight exists.
    flight = Flight.query.get(flight_id)
    if not flight:
        return render_template("error.html", message="No such flight with that id.")

    # Add passenger.
    flight.add_passenger(name)
    return render_template("success.html")


@app.route("/submitreview")
@login_required
def bookinfo():
    return "Book information: TODO"

@app.route("/submitreview")
@login_required
def submitreview():
    return "Submit review: TODO"



@app.route("/demo")
@login_required
def demo():
    flights = Flight.query.all()
    return render_template("demo.html", flights=flights)


@app.route("/flights")
def flights():
    """List all flights."""
    flights = Flight.query.all()
    return render_template("flights.html", flights=flights)


@app.route("/flights/<int:flight_id>")
def flight(flight_id):
    """List details about a single flight."""

    # Make sure flight exists.
    flight = Flight.query.get(flight_id)
    if flight is None:
        return render_template("error.html", message="No such flight.")

    # Get all passengers.
    passengers = flight.passengers
    return render_template("flight.html", flight=flight, passengers=passengers)


@app.route("/api/flights/<int:flight_id>")
def flight_api(flight_id):
    """Return details about a single flight."""

    # Make sure flight exists.
    flight = Flight.query.get(flight_id)
    if flight is None:
        return jsonify({"error": "Invalid flight_id"}), 422

    # Get all passengers.
    passengers = flight.passengers
    names = []
    for passenger in passengers:
        names.append(passenger.name)
    return jsonify({
            "origin": flight.origin,
            "destination": flight.destination,
            "duration": flight.duration,
            "passengers": names
        })
