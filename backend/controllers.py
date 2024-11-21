from flask import render_template, url_for, redirect, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from flask import current_app as app
from backend.modals import *
from sqlalchemy import or_

# Home page
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
                    return redirect(url_for("user_page", button_state=1))
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
    profesionals = User.query.filter_by(role=2)
    return render_template("admin_dashboard.html", services=services, profesionals=profesionals)

# Adding a service 
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


# Editing a service 
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

# Deleting(deactivating) a service
@app.route("/delete_service/<service_id>")
def delete_service(service_id):
    service = get_service_obj(service_id)
    service.status = 0
    db.session.commit()
    flash("Service deleted", category="danger")

    return redirect(url_for("admin_page"))

# Toggle funtionality for blocking/unblocking of Users
@app.route("/professional_status/<user_id>", methods=["GET", "POST"])
def status_changer(user_id):
    if request.method == "POST":
        user = User.query.filter_by(id=user_id).first()
        if user.status: # status = 1
            user.status = 0
        else:
            user.status = 1
        db.session.commit()

        return redirect(url_for("admin_page"))
    return redirect(url_for("admin_page"))





# User dashboard
@app.route("/user/<int:button_state>", methods=["GET", "POST"])
def user_page(button_state): # button_state: 0:user_requests_tab, 1:user_services_tab
    if button_state:
        return redirect(url_for("user_services_tab"))
    else:
        return redirect(url_for("user_requests_tab"))

# User services tab
@app.route("/user/services", methods=["GET", "POST"])
def user_services_tab():
    button_state = request.args.get("button_state", 1, type=int) # Accessing data send using url_for function, default=1
    services = Service.query.filter_by(status=1)
    return render_template("user_services_tab.html", services=services, button_state=button_state)

# User create service request
@app.route("/user/services/create_request/<int:service_id>", methods=["GET", "POST"])
def create_request(service_id):
    customer_id = current_user.id
    service_request = ServiceRequest(service_id=service_id, customer_id=customer_id)
    try:
        db.session.add(service_request)
        db.session.commit()
        flash("Service requested successfuly.", category="info")

        return redirect(url_for("user_services_tab"))
    except Exception as e:
        print(e)
        db.session.rollback()

        flash("Service request failed.", category="danger")

    return redirect(url_for("user_services_tab"))



# User requests tab
@app.route("/user/requests", methods=["GET", "POST"])
def user_requests_tab():
    button_state = request.args.get("button_state", 0, type=int) # Accessing data, sent to us, using url_for function, default=0
    service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id==current_user.id, ServiceRequest.status==0).all()
    approved_service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id==current_user.id, ServiceRequest.status==1).all()
    completed_service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id==current_user.id, or_(ServiceRequest.status==2, ServiceRequest.status==3)).all()

    return render_template("user_requests_tab.html", service_requests=service_requests, button_state=button_state, approved_service_requests=approved_service_requests, completed_service_requests=completed_service_requests)

# User cancel request
@app.route("/cancel_request/<int:request_id>", methods=["GET", "POST"])
def cancel_request(request_id):
    service_request = ServiceRequest.query.get(request_id)
    try: 
        db.session.delete(service_request)
        db.session.commit()
        flash("Service request deleted successfuly.", category="info")

        return redirect(url_for("user_requests_tab"))
    except:
        db.session.rollback()
        flash("Service request not deleted", category="danger")
    
    return redirect(url_for("user_requests_tab"))

# User feedback page
@app.route("/user/service_feedback/<int:service_id>", methods=["GET", "POST"])
def user_feedback_page(service_id):
    service_request = ServiceRequest.query.get(service_id)

    if request.method == "POST":
        remarks = request.form.get("remarks")
        rating = request.form.get("rating")
        
        try:
            service_request.set_endtime()
            service_request.status = 2
            service_request.rating = rating
            service_request.remarks = remarks
            db.session.commit()
            flash("Thankyou for your response.", category="info")

            return redirect(url_for("user_requests_tab"))
        except:
            db.session.rollback()
            flash("Something went wrong.", category="danger")
    
    return render_template("user_service_feedback.html", service_request=service_request)

# Service request full info page
@app.route("/service_request_info/<int:id>")
def service_request_info(id):
    print(type(id))
    service_request = ServiceRequest.query.get(id)
    return render_template("service_request_info.html", service_request=service_request)




# Professional dashboard
@app.route("/professional", methods=["GET", "POST"])
def professional_page(): 
    service_type_id = current_user.professional_info.service_type # Accessing current user's service type(id)
    requested_service_requests = ServiceRequest.query.filter(ServiceRequest.service_id==service_type_id, ServiceRequest.status==0).all()
    accepted_service_requests = ServiceRequest.query.filter(ServiceRequest.professional_id==current_user.professional_info.id, or_(ServiceRequest.status==1, ServiceRequest.status==2)).all() 
    completed_service_requests = ServiceRequest.query.filter(ServiceRequest.professional_id==current_user.professional_info.id, ServiceRequest.status==3).all() 

    return render_template("professional_dashboard.html", requested_service_requests=requested_service_requests, accepted_service_requests=accepted_service_requests, completed_service_requests=completed_service_requests)

# Accept request
@app.route("/accept_request/<int:request_id>", methods=["GET", "POST"])
def accept_request(request_id):
    service_request = ServiceRequest.query.get(request_id)
    service_request.professional_id = current_user.professional_info.id # Assigning the current professional to the job
    service_request.status = 1 # changing the status to accepted
    try:
        db.session.commit()
        flash("Job accepted successfuly.", category="info")
        return redirect(url_for("professional_page"))
    except:
        db.session.rollback()
        flash("Something went wrong! Job not assigned.", category="danger")

    return redirect(url_for("professional_page"))

# Service request Completion 
@app.route("/service_completed/<int:service_request_id>", methods=["GET", "POST"])
def service_completed(service_request_id):
    service_request = ServiceRequest.query.get(service_request_id)
    customer = User.query.get(service_request.customer_id)
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        try:
            customer.update_rating(rating)
            service_request.status = 3
            db.session.commit()
            flash("Service done successfuly.", category="info")
        except:
            db.session.rollback()
            flash("Something went wrong.", category="danger")
    return redirect(url_for("professional_page"))



# Customer registration
@app.route("/signup")
def signup_page():
    return render_template("signup.html")

# Professional registration
@app.route("/professional_signup")
def professional_signup_page():
    services = Service.query.filter_by(status=1) # Passed for sevice type selection by a professional
    return render_template("professional_signup.html", services=services)

# New user registration
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
            flash("Account created successfuly.", category="info" )

            return redirect(url_for("login_page"))
        except:
            db.session.rollback()
            flash("Something went wrong. Try again!!!", category="danger")

    return redirect(url_for("signup_page"))

# New professional registration
@app.route("/professional_registration", methods=["GET", "POST"])
def professional_registration_page():
    if request.method == "POST":
        # Grabing data form form
        role = 2 # For Professionals
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        service_type = request.form.get("service_type")
        experience = request.form.get("experience")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        status = 0
        # Setting up new user
        try:
            # First creating a user then using it id to make a professional
            new_user = User(email=email, password=password, name=name, address=address, pincode=pincode, role=role, status=status)
            db.session.add(new_user)
            db.session.flush() # To get user.id 
            # professional created
            new_pro = Professional(user_id=new_user.id, service_type=service_type, experience=experience)
            db.session.add(new_pro)
            db.session.commit()
            flash("Professional account created successfuly", category="info")

            return redirect(url_for("login_page"))
        except:
            db.session.rollback()
            flash("Something went wrong. Try again!!!", category="danger")

    return redirect(url_for("professional_signup_page"))


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