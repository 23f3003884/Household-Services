from flask import Flask


app = None #Global variable

def setup_app(): #Initializations
    app = Flask(__name__)
    app.app_context().push() #Direct access to other modules
    app.debug=True

setup_app() # initializing app

from backend.controllers import * # Importing routes


if __name__ == "__main__":
    app.run()