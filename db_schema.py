from enum import unique
from flask_sqlalchemy import SQLAlchemy
from werkzeug import security
import datetime
from sqlalchemy.inspection import inspect

# create the database interface
db = SQLAlchemy()

# for the login properties and methods (is_authenticated, etc.)
# UserMixin supports login features
from flask_login import UserMixin

# a model of a user for the database
class User(UserMixin, db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(30))
    bills = db.relationship('Bills', backref='user', lazy='dynamic')
    bill_completion = db.relationship('User_Bill', backref='User_completion', lazy='dynamic')
    notfications = db.relationship('Notfications', backref='user_notfications', lazy='dynamic')
    house_members = db.relationship('Households', backref='house_members', lazy='dynamic')
    email = db.Column(db.String(30))

    def __init__(self, username, password_hash, email):  
        self.username=username
        self.password_hash=password_hash
        self.email=email

# a model of a list for the database
# it refers to a Bills
class Bills(db.Model):
    __tablename__='bills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    amount = db.Column(db.Integer())
    shared_with = db.Column(db.Text())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))  # this ought to be a "foreign key"
    completion= db.Column(db.Boolean)
    bill_completion = db.relationship('User_Bill', backref='bills_completion', lazy='dynamic')


    def __init__(self, name,amount, user_id,shared_with, completion):
        self.name=name
        self.amount = amount
        self.user_id = user_id
        self.shared_with = shared_with
        self.completion = completion

# a table that refers to each user completion of a bill
class User_Bill(db.Model):
    __tablename__ = 'completion'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    bill_id = db.Column(db.Integer(), db.ForeignKey('bills.id'))
    user_bill_completion= db.Column(db.Boolean)

    def __init__(self,user_id,bill_id,user_bill_completion):
        self.user_id = user_id
        self.bill_id = bill_id
        self.user_bill_completion = user_bill_completion

# a table that refers to the notfication sent to users
class Notfications(db.Model):
    __tablename__ = 'notfications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    notfication =db.Column(db.Text())

    def __init__(self,user_id,notfication):
        self.user_id = user_id
        self.notfication = notfication

# a table that refers to the households and their members
class Households(db.Model):
    __tablename__ = 'households'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    name = db.Column(db.Text())
    members = db.Column(db.Text())
    number_of_members = db.Column(db.Integer())
        
    def __init__(self,user_id,name,members,number_of_members):
        self.user_id = user_id
        self.name = name
        self.members = members
        self.number_of_members = number_of_members


# put some data into the tables
def dbinit():
    # commit all the changes to the database file
    db.session.commit()