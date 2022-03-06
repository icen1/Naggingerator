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
    email = db.Column(db.String(30))

    def __init__(self, username, password_hash, email):  
        self.username=username
        self.password_hash=password_hash
        self.email=email

# a model of a list for the database
# it refers to a user
class Bills(db.Model):
    __tablename__='bills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    amount = db.Column(db.Integer())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))  # this ought to be a "foreign key"
    users_with_bill = db.Column(db.Text(), db.ForeignKey('users.id'))
    completion= db.Column(db.Boolean,db.ForeignKey('bills.id'),db.ForeignKey('users.id'))

    def __init__(self, name,amount, user_id,users_with_bill, completion):
        self.name=name
        self.amount = amount
        self.user_id = user_id
        self.users_with_bill = users_with_bill
        self.completion = completion
# put some data into the tables
def dbinit():
    # commit all the changes to the database file
    db.session.commit()