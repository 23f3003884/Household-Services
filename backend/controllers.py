from flask import render_template, url_for
from flask import current_app as app


@app.route("/")
def home_page():
    return render_template('index.html')


@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/professional_signup")
def professional_signup_page():
    return render_template("professional_signup.html")