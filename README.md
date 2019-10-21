# Project 1: Book reviews

Web Programming with Python and JavaScript
Project 1: Book review site

# Goal and overview

The site offers the possibility for users to submit reviews on a large number of books, as well as see reviews of other users and information of GoodReads on the selected book(s). Developers have the possibility to retrieve information on reviews from the site.

# Navigation

After registration and login, the user is guided through the following steps:
- search for a book with ISBN, author or title or combination thereof,
- select a book from a list of books that match the given criteria,
- read info and reviews from other users of the selected book and submit a review oneself,
- confirmation of successful submission of review and possibility to submit another review.

In the program this means the following dialogue:
- (client) index page "/" with search fields
- (server) hands over to function "search" that searches matching books in the database
- (client) list of books that match criteria with possibility to select, on page "selectconfirm.html"
- (server) hands over to function "infoforreview" which gathers information from GoodReads and reviews from other users
- (client) present this information to user and offers possibility to submit a review, on page "infoforreview.html"
- (server) function "submitreview" inserts the review in the database, with corresponding book id and user id
- (client) page "reviewsuccess.html" confirms successful submission and offers possibility to submit another review

# API

In addition to this, developers from third parties can retrieve information on submitted reviews via the URL /API/<"ISBN-number">, where "ISBN-number" is a string with the 10-digit ISBN-number of the requested book. The response contains the book’s title, author, publication date, ISBN number, review count, and average score.The response has the form of a JSON-string with the following format:
{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}

# Technology and languages

Languages: Python, PostgreSQL, jinja2, Flask, SQLAlchemy
Database is on Heroku
