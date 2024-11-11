from flask import Flask
from backend.modals import db, User 
from flask_login import LoginManager



app = None #Global variable

def setup_app(): #Initializations
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///household_services.sqlite3" # Database file name
    app.config["SECRET_KEY"] = "123456"
    db.init_app(app) # Connecting database to flask app
    app.app_context().push() #Direct access to other modules
    login_manager = LoginManager(app) # For manageing user sessions
    login_manager.login_view = "login_page" # Redirect to "login_page" route funtion if some try to access restricted route 
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))



    app.debug=True

setup_app() # initializing app



from backend.controllers import * # Importing routes


if __name__ == "__main__":
    app.run()