from flask import render_template, url_for, redirect, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from flask import current_app as app
from backend.modals import *
from sqlalchemy import or_
import matplotlib.pyplot as plt

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
                if usr.status:
                    login_user(usr) # added user to app session
                    # Separating users based on their roles
                    if usr.role == 0:
                        return redirect(url_for("admin_page", button_state=0))
                    elif usr.role == 1:
                        return redirect(url_for("user_page", button_state=1))
                    else:
                        return redirect(url_for("professional_page"))
                else:
                    flash("Account is blocked/under verification. Contact admin for support(manish@gmail.com).", category="danger")
            else:
                flash("Wrong password.", category="danger")
        else:
            flash("Invalid email address.", category="danger")

    return render_template("login.html")

# User Summary/info
@app.route("/user_info")
def user_info():
    if current_user.role==0:
        plot = get_plt_user_stats()
        if plot:
            plot.savefig("./static/image/plots/users_summery.jpeg")
            plot.clf()

        plot = get_plt_services_stats()
        if plot:
            plot.savefig("./static/image/plots/services_summery.jpeg")
            plot.clf()
    else:
        plot = get_plt_ratings()
        if plot:
            plot.savefig("./static/image/plots/rating_summery.jpeg")
            plot.clf()

        plot = get_plt_service_rating()
        if plot:
            plot.savefig("./static/image/plots/service_rating_summery.jpeg")
            plot.clf()


    return render_template("user_info.html")


# Admin dashboard
@app.route("/admin/<int:button_state>", methods=["GET", "POST"]) #Button state: 0-Services, 1-Users, 2-Requests
@login_required
def admin_page(button_state):
    if button_state==0: # Services
        return redirect(url_for("services_tab_page"))
    elif button_state==1: # Users 
        return redirect(url_for("users_tab_page"))
    else: # Requests
        return redirect(url_for("requests_tab_page"))
    
# Search funtionality
@app.route("/admin/search", methods=["GET", "POST"])
def admin_search():
    button_state=request.args.get("button_state", type=int)
    if request.method=="POST":
        search_text = request.form.get("search_text")
        if button_state==0:
            services = Service.query.filter(Service.name.ilike(f"%{search_text}%")).all()
            
            return render_template("services_tab.html", button_state=button_state, services=services)
        elif button_state==1:
            filter_option = request.form.get("filter_option")
            if filter_option=="name":
                users = User.query.filter(User.name.ilike(f"%{search_text}%")).all()
            elif filter_option=="email":
                users = User.query.filter(User.email.ilike(f"%{search_text}%")).all()
            elif filter_option=="service_type":
                pro = Professional.query.join(Service).filter(Service.name.ilike(f"%{search_text}%")).all()
                users = [x.user for x in pro]
            else: # status
                if search_text.lower() in ["inactive", "0", "blocked"]:
                    search_text=0
                else: #active
                    search_text=1
                users = User.query.filter(User.status.ilike(f"%{search_text}%")).all()
            
            return render_template("admin_user_search_results.html", button_state=button_state, users=users)
        else:
            filter_option = request.form.get("filter_option")
            if filter_option=="name":
                requests = ServiceRequest.query.join(User).filter(User.name.ilike(f"%{search_text}%")).all()
            elif filter_option=="pro_name":
                pro = Professional.query.join(User).filter(User.name.ilike(f"%{search_text}%")).first()
                requests = ServiceRequest.query.join(Professional).filter(Professional.id==pro.id).all()
            elif filter_option=="address":
                requests = ServiceRequest.query.join(User).filter(User.address.ilike(f"%{search_text}%")).all()
            else: # status
                if search_text.lower()=="requested":
                    search_text=0
                elif search_text.lower()=="accepted":
                    search_text=1
                else:
                    search_text=3
                requests = ServiceRequest.query.filter(ServiceRequest.status==search_text).all()
                
            return render_template("requests_tab.html", button_state=button_state, requests=requests)
        

    return redirect(url_for("admin_page", button_state=button_state))
    


# Services Tab page
@app.route("/admin/services", methods=["GET", "POST"])
def services_tab_page():
    button_state = 0 # Sets default button_state
    services = Service.query.filter_by(status=1)
    
    return render_template("services_tab.html", button_state=button_state, services=services)

# Users Tab page
@app.route("/admin/users", methods=["GET", "POST"])
def users_tab_page():
    button_state = 1
    users = User.query.filter(or_(User.role==1, User.role==2))
    return render_template("users_tab.html", button_state=button_state, users=users)

# Show professional photo
@app.route("/admin/photo")
def show_photo():
    user_id = request.args.get("user_id", type=int)
    path =  f"image/uploads/{user_id}.jpeg"
    return render_template("photo.html", path=path)

# Requests Tab page
@app.route("/admin/requests", methods=["GET", "POST"])
def requests_tab_page():
    button_state = 2
    requests = ServiceRequest.query.all()
    return render_template("requests_tab.html", button_state=button_state, requests=requests)



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
        
            return redirect(url_for("admin_page", button_state=0))
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
           
            return redirect(url_for("admin_page", button_state=0))
        except:
            db.session.rollback() # If something goes wrong above it will undo that
            flash("Something went wrong.", category="danger")
    
    return render_template("edit_service.html", service=service, button_state=0)

# Deleting(deactivating) a service
@app.route("/delete_service/<service_id>")
def delete_service(service_id):
    service = get_service_obj(service_id)
    service.status = 0
    db.session.commit()
    flash("Service deleted", category="danger")

    return redirect(url_for("admin_page", button_state=0))

# Toggle funtionality for blocking/unblocking of Users
@app.route("/user_status/<user_id>", methods=["GET", "POST"])
def status_changer(user_id):
    if request.method == "POST":
        user = User.query.filter_by(id=user_id).first()
        if user.status: # status = 1
            user.status = 0
        else:
            user.status = 1
        db.session.commit()

    return redirect(url_for("admin_page", button_state=1))





# User dashboard
@app.route("/user/<int:button_state>", methods=["GET", "POST"])
def user_page(button_state): # button_state: 0:user_requests_tab, 1:user_services_tab
    if button_state:
        return redirect(url_for("user_services_tab"))
    else:
        return redirect(url_for("user_requests_tab"))
    
# Search funtionality
@app.route("/user/search", methods=["GET", "POST"])
def user_search():
    button_state=request.args.get("button_state", type=int)
    if request.method=="POST":
        search_text = request.form.get("search_text")
        filter_option = request.form.get("filter_option")
        if button_state==1:
            if filter_option=="name":
                services = Service.query.filter(Service.name.ilike(f"%{search_text}%")).all()
            else:
                services = Service.query.filter(Service.desc.ilike(f"%{search_text}%")).all()

            return render_template("user_services_tab.html", button_state=button_state, services=services)

    return redirect(url_for("user_page", button_state=button_state))

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
            flash("Thank you for your response.", category="info")

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
    if current_user.professional_info.ready_for_work():
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
    else:
        flash("Accepted jobs limit reached.", category="danger")

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
            #Creating photo url with user_id
            file = request.files["uploaded_file"]
            if file.filename:
                url = f"./static/image/uploads/{new_user.id}.jpeg"
                file.save(url)
            # professional created
            new_pro = Professional(user_id=new_user.id, service_type=service_type, experience=experience)
            db.session.add(new_pro)
            db.session.commit()

            

            flash("Professional account created successfuly", category="info")

            return redirect(url_for("login_page"))
        except Exception as e:
            print(e)
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

# Numbers of Customers and Users on website
def get_plt_user_stats():
    plt.style.use('dark_background')

    total_users = len(User.query.filter(or_(User.role==1,User.role==2)).all())
    customers = len(User.query.filter(User.role==1).all())
    professonals = len(User.query.filter(User.role==2).all())

    try:
        if total_users > 0:
            frac_cust = (customers/total_users)*100
            frac_pro = (professonals/total_users)*100
        else:
            frac_cust = 0
            frac_pro = 0

        data = [frac_cust, frac_pro]
        labels = ["Customers", "Professtionals"]
        plt.pie(data, labels=labels)
        plt.title("Users Summary")
        return plt
    except:
        pass

# Services Stats
def get_plt_services_stats():
    plt.style.use('dark_background')

    try:
        # Services list
        services_list = []
        services_counts = [] # Numbers of requests of respective service type
        services = Service.query.all()
        for service in services:
            services_list.append(service.name)
            services_counts.append(len(service.service_requests))

        plt.bar(services_list, services_counts)
        plt.title("Services Summary")
        plt.xlabel("Services Type")
        plt.ylabel("No. of requests")
        return plt
    except:
        pass

#Ratings chart
def get_plt_ratings():
    plt.style.use('dark_background')


    try:
        rating = current_user.update_ratings()

        good = (rating/5)*100
        bad = 100-good

        data = [good, bad]
        labels = ["Good", "Bad"]
        plt.pie(data, labels=labels)
        plt.title(f"behaviour: {good}")
        return plt
    except:
        pass
    
# Service rating
def get_plt_service_rating():
    try:
        if current_user.professional_info:
            ser_reqs = current_user.professional_info.service_requests
        else:
            ser_reqs = current_user.service_requests

        services_req_list = []
        services_req_counts = []
        for ser_req in ser_reqs:
            services_req_list.append(str(ser_req.id))
            if ser_req.rating:
                services_req_counts.append(ser_req.rating)
            else:
                services_req_counts.append(0)

        print("ids",services_req_list)
        print("ratings", services_req_counts)
        plt.bar(services_req_list, services_req_counts)
        plt.title("Services Summary")
        plt.xlabel("Service Request Id")
        plt.ylabel("Rating")
        return plt
    except:
        pass


admin = User(email="manish@gmail.com", password="123456", role=0, name="Manish kumar", address="Nihal Vihar", pincode=110041)


