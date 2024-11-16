from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin


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

    # Relations
    service_requests = db.relationship("ServiceRequest", cascade="all, delete", backref="customer", lazy=True) # For accessing all the service requests created by a user(customer)
    professional_info = db.relationship("Professional", cascade="all, delete", backref="user", uselist=False) # one to one relation for accessing futher professional info 

    # Make every first leter of word capitalized
    def capitalised_name(self):
        return self.name.title()

class Professional(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"),unique=True, nullable=False) #Foreign key - from User table
    service_type = db.Column(db.Integer(), db.ForeignKey("service.id"), nullable=False) #Foreign Key - from Service table
    experience = db.Column(db.Integer(), nullable=False)
    rating = db.Column(db.Integer(), nullable=False)
    # Relations
    service = db.relationship("Service", backref="professionals", lazy=True)


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
    professional_id = db.Column(db.Integer(), db.ForeignKey("professional.id"), nullable=True) # Foreign Key - Professional table, One professional for one job
    start_date = db.Column(db.DateTime(), nullable=False, default=func.now()) # func.now():get current time
    end_date = db.Column(db.DateTime(), nullable=False)
    status = db.Column(db.Integer(), nullable=False, default=0) # 0-requested, 1-accepted, 2-completed
    rating = db.Column(db.Integer(), nullable=False) # Mandatory to give ratings for closing the job
    remarks = db.Column(db.String(500))
    # Relations
    professional = db.relationship("Professional", backref="service_requests", lazy=True)

    # Finds professional assigned to the job
    def get_professional(self):
        professional = self.professional
        if professional:
            return professional.name
        else:
            return "Unassigned"
        
    # Status decoder
    def get_status(self):
        status = self.status
        if status == 0:
            return "Requested"
        elif status == 1:
            return "Accepted"
        else:
            return "Completed"
            
