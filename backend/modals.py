from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.Integer(), nullable=False, default=1) # 0-Admin, 1-Customer, 2-Professional
    name = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.Integer(), nullable=False)
    status = db.Column(db.Integer(), nullable=False, default=1) # 0-inactive, 1-active
    rating = db.Column(db.Integer(), default=0)
        
    # Relations
    service_requests = db.relationship("ServiceRequest", cascade="all, delete", backref="customer", lazy=True) # For accessing all the service requests created by a user(customer)
    professional_info = db.relationship("Professional", cascade="all, delete", backref="user", uselist=False) # one to one relation for accessing futher professional info 

    # Make every first leter of word capitalized
    def capitalised_name(self):
        return self.name.title()
    
    # Update rating
    def update_rating(self, rating):
        if not self.rating:
            self.rating = 0
        self.rating = int((self.rating + rating)/2)

    # Funtion to update ratings of professionals 
    def update_ratings(self):
        if self.professional_info:
            ser_reqs = self.professional_info.service_requests
            number_of_services_req = len(ser_reqs)
            rating = 0
            for ser_req in ser_reqs:
                if ser_req.rating:
                    rating += ser_req.rating
            if number_of_services_req:
                self.rating = rating//number_of_services_req
            db.session.commit()




class Professional(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"),unique=True, nullable=False) #Foreign key - from User table
    service_type = db.Column(db.Integer(), db.ForeignKey("service.id"), nullable=False) #Foreign Key - from Service table
    experience = db.Column(db.Integer(), nullable=False)
    
    # Relations
    service = db.relationship("Service", backref="professionals", lazy=True)

    # Ready for work 
    def ready_for_work(self):
        service_request = self.service_requests # Accepted jobs limited to 2
        if service_request:
            if len(service_request) > 2:
                return False
        return True


class Service(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(30),unique=True, nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    time_required = db.Column(db.Integer(), nullable=False) # Time required (in Hrs)
    price = db.Column(db.Float(), nullable=False)
    status = db.Column(db.Integer(), nullable=False, default=1) # 0-inactive, 1-active

    # Relations
    service_requests = db.relationship("ServiceRequest", cascade="all, delete", backref="services", lazy=True) # For accessing all the service requests having common service

    # Make every first leter of word capitalized
    def capitalised_name(self):
        return self.name.title()

class ServiceRequest(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    service_id = db.Column(db.Integer(), db.ForeignKey("service.id"), nullable=False) # Foreign Key - Service table
    customer_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False) #Foreign key - from User(Customer) table
    professional_id = db.Column(db.Integer(), db.ForeignKey("professional.id")) # Foreign Key - Professional table, One professional for one job
    start_date = db.Column(db.DateTime(), nullable=False, default=datetime.now().replace(microsecond=0)) # datetime.now():get current time
    end_date = db.Column(db.DateTime())
    status = db.Column(db.Integer(), nullable=False, default=0) # 0-requested, 1-accepted, 2-completed at users-end, 3-completed at professionals-end
    rating = db.Column(db.Integer()) # Mandatory to give ratings for closing the job/tasks
    remarks = db.Column(db.String(500))
    # Relations
    professional = db.relationship("Professional", backref="service_requests", lazy=True)

    # Finds professional assigned to the job
    def get_professional(self):
        professional = self.professional
        if professional:
            return professional.user.name
        else:
            return "Unassigned"
        
    # Finds customer name 
    def get_customer(self):
        return self.customer.name
        
        
    # Status decoder
    def get_status(self):
        status = self.status
        if status == 0:
            return "Requested"
        elif status == 1:
            return "Accepted"
        else:
            return "Completed"
        
    # Service complition time setter
    def set_endtime(self):
        self.end_date = datetime.now().replace(microsecond=0)
            
