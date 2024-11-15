from flask import render_template, url_for, redirect, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from flask import current_app as app
from backend.modals import *


@app.route("/")
def home_page():
    return render_template('index.html')

# Login page
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Grabing first user with given email
        usr = User.query.filter_by(email=email).first()
        if usr:
            if usr.password == password:
                login_user(usr) # added user to app session
                # Separating users based on their roles
                if usr.role == 0:
                    return redirect(url_for("admin_page"))
                elif usr.role == 1:
                    return redirect(url_for("user_page"))
                else:
                    return redirect(url_for("professional_page"))
            else:
                flash("Wrong password.", category="danger")
        else:
            flash("Invalid email address.", category="danger")

    return render_template("login.html")


# Admin dashboard
@app.route("/admin")
@login_required
def admin_page():
    services = Service.query.filter_by(status=1)
    return render_template("admin_dashboard.html", services=services)

# Route for adding a service 
@app.route("/add_service", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        name = request.form.get("name")
        desc = request.form.get("desc")
        price = request.form.get("price")
        time_required = request.form.get("time_required")
        try:
            new_service = Service(name=name, desc=desc, price=price, time_required=time_required)
            db.session.add(new_service)
            flash("Service added successfully.", category="info")
            db.session.commit()
        
            return redirect(url_for("admin_page"))
        except:
            db.session.rollback() # If something goes wrong above it will undo that
            flash("Something went wrong.", category="danger")
    
    return render_template("add_service.html")


# Route for editing a service 
@app.route("/edit_service/<service_id>", methods=["GET", "POST"])
def edit_service(service_id):
    service = get_service_obj(service_id) # 0:None, Other than 0:means data present therfore UPDATE 

    if request.method == "POST":
        name = request.form.get("name")
        desc = request.form.get("desc")
        price = request.form.get("price")
        time_required = request.form.get("time_required")
        try:
            if service: # If there is a service obj then UPDATE 
                service.name = name
                service.desc = desc
                service.price = price
                service.time_required = time_required
                flash("Service updated successfully.", category="info")
                db.session.commit()
           
            return redirect(url_for("admin_page"))
        except:
            db.session.rollback() # If something goes wrong above it will undo that
            flash("Something went wrong.", category="danger")
    
    return render_template("edit_service.html", service=service)

# Route for deleting(deactivating) a service
@app.route("/delete_service/<service_id>")
def delete_service(service_id):
    service = get_service_obj(service_id)
    service.status = 0
    db.session.commit()
    flash("Service deleted", category="danger")

    return redirect(url_for("admin_page"))


# User dashboard
@app.route("/user")
def user_page():
    return render_template("user_dashboard.html")

# Professional dashboard
@app.route("/professional")
def professional_page():
    return render_template("professional_dashboard.html")


@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/professional_signup")
def professional_signup_page():
    return render_template("professional_signup.html")

# Route for new user registration
@app.route("/customer_registration", methods=["GET", "POST"])
def customer_registration_page():
    if request.method == "POST":
        # Grabing data form form
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        # Setting up new user
        try:
            new_user = User(email=email, password=password, name=name, address=address, pincode=pincode)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for("login_page"))
        except:
            flash("Something went wrong. Try again!!!", category="danger")

    return redirect(url_for("signup_page"))


# Logout route
@app.route("/logout")
def logout():
    logout_user()
    flash("You have been loged out.", category="info")
    return redirect(url_for("home_page"))



# Helper Funtions

# Returns Service Obj
def get_service_obj(service_id):
    obj = Service.query.filter_by(id=service_id).first()
    return obj