import os
import csv
import json
import requests

from flask import Flask, session, request, flash, jsonify, redirect, render_template, abort
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

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    """Search for books"""
    return render_template("index.html")


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
            flash("Passwords should be at least eight and at most 30 characters long, contain one digit, one uppercase and one lowercase letter and one of the symbols $@#%&_")
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

        if rows is not None:
            flash("Username already exists")
            return render_template("register.html")

        # Insert username and password hash into database
        db.execute("INSERT INTO users (username, pw_hash) VALUES (:username, :pw_hash)",
                   {"username": username, "pw_hash": generate_password_hash(password)})
        db.commit()

        # Retrieve the id from the user
        id = db.execute("SELECT user_id FROM users WHERE username = :username",
                        {"username": username}).fetchone()["user_id"]

        # Remember the id of the user who has just registered
        session["user_id"] = id

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
            return render_template("login.html")
        else:
            if not check_password_hash(rows["pw_hash"], request.form.get("password")):
                flash("Invalid password")
                return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows["user_id"]

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


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search books"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted

        isbn = request.form.get("isbn")
        author = request.form.get("author")
        title = request.form.get("title")

        if not isbn and not author and not title:
            flash("Please enter ISBN number or author or title")
            return render_template("index.html")

        if not isbn:
            isbn = ""
        if not author:
            author = ""
        else:
            author = author.lower()
        if not title:
            title = ""
        else:
            title = title.lower()

        # Query database for username to check it doesn't exist already
        rows = db.execute("SELECT * FROM books WHERE POSITION(:isbn IN books.isbn) > 0 AND POSITION(:author IN LOWER(books.author)) > 0 AND POSITION(:title IN LOWER(books.title)) > 0",
                          {"isbn": isbn, "author": author, "title": title}).fetchall()

        if rows is None:
            flash("No books found with this ISBN, author and title")
            return render_template("index.html")

        return render_template("selectconfirm.html", rows = rows)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html")


@app.route("/infoforreview", methods=["GET", "POST"])
@login_required
def infoforreview():
    if request.method == "POST":

        # personal key given by GoodReads
        key = "Bfq3f3uZuPfGtfElArpA"

        book_id = request.form.get("book_id")
        if not book_id:
            flash("Invalid book ID")
            return redirect("/")

        book = db.execute("SELECT * FROM books WHERE book_id = :book_id",
                          {"book_id": book_id}).fetchone()
        isbn = book["isbn"]

        # convert ISBN10 tot ISBN13
        checksum = (10 - (9 + 3*7 + 8 + 3*int(isbn[0]) + int(isbn[1]) + 3*int(isbn[2]) + int(isbn[3]) + 3*int(isbn[4]) + int(isbn[5]) + 3*int(isbn[6]) + int(isbn[7]) + 3*int(isbn[8])) % 10) % 10
        isbns = "978" + isbn[0:9] + str(checksum)

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbns})
        if res:
            book_info = res.json()["books"][0]

        results = db.execute("SELECT user_id, review FROM reviews WHERE book_id = :book_id",
                             {"book_id": book_id}).fetchall()
        reviews = []
        # tranform results into array of dicts and add username to reviews, so that it can be passed to the web page
        for result in results:
            review = dict(result)
            temp = db.execute("SELECT username FROM users WHERE user_id = :user_id",
                       {"user_id": review["user_id"]}).fetchone()
            review.update({"username": temp["username"]})
            reviews.append(review)

        return render_template("infoforreview.html", book = book, book_info = book_info, reviews = reviews)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return redirect("/")


@app.route("/submitreview", methods=["GET", "POST"])
@login_required
def submitreview():
    if request.method == "POST":

        # TO DO: get review and user_id
        user_id = session["user_id"]
        username = db.execute("SELECT username FROM users WHERE user_id = :user_id",
                                  {"user_id": user_id}).fetchone()["username"]

        rating = request.form.get("rate")
        if rating is None:
            flash("Please submit rating")
            return redirect("/")
        book_id = request.form.get("book_id")
        review = request.form.get("reviewtext")

        # Insert username and password hash into database
        db.execute("INSERT INTO reviews (user_id, book_id, rating, review) VALUES (:user_id, :book_id, :rating, :review)",
                   {"user_id": user_id, "book_id": book_id, "rating": rating, "review": review})
        db.commit()

        return render_template("reviewsuccess.html", username = username)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html")


@app.route("/api/<isbn>")
def flight_api(isbn):
    """Return details about a book with a given ISBN10"""

    # Make sure the ISBN is valid
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).fetchone()
    print(book)
    if not book:
        # invalid isbn or isbn not in database
        abort(404, "ISBN number not found")

    reviews = db.execute("SELECT rating FROM reviews WHERE book_id = :book_id",
                         {"book_id": book.book_id}).fetchall()
    print(reviews)
    review_count = len(reviews)

    if review_count == 0:
        average_score = 0
    else:
        # calculate sum of all ratings
        sum = 0
        for review in reviews:
            sum += review.rating
        average_score = sum/review_count

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": isbn,
            "review_count": review_count,
            "average_score": average_score
            })
