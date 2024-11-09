from flask import Flask, render_template
from flask import current_app as app


@app.route("/")
def login_page():
    return render_template('login.html')