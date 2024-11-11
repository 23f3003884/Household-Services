from flask import Flask
from backend.modals import db 



app = None #Global variable

def setup_app(): #Initializations
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///household_services.sqlite3" # Database file name
    db.init_app(app) # Connecting database to flask app
    app.app_context().push() #Direct access to other modules

    app.debug=True

setup_app() # initializing app

from backend.controllers import * # Importing routes


if __name__ == "__main__":
    app.run()