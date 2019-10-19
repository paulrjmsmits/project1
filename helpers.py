import os
import requests
import urllib.parse

from flask import flash, redirect, render_template, request, session
from functools import wraps


def password_check(passwd):
    """Check if password fulfils validation requirements."""
    SpecialSym = ['$', '@', '#', '%', '&', '_']
    val = True

    if len(passwd) < 8 or len(passwd) > 30 or not any(char.isdigit() for char in passwd) \
       or not any(char.isupper() for char in passwd) or not any(char.islower() for char in passwd) \
       or not any(char in SpecialSym for char in passwd):
    	val = False
    return val


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        print(session.get("user_id"))
        return f(*args, **kwargs)
    return decorated_function
