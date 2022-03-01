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
    lists = db.relationship('List', backref='user', lazy='dynamic')
    email = db.Column(db.String(30))

    def __init__(self, username, password_hash, email):  
        self.username=username
        self.password_hash=password_hash
        self.email=email

# a model of a list for the database
# it refers to a user
class List(db.Model):
    __tablename__='lists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))  # this ought to be a "foreign key"
    items = db.relationship('ListItem', backref='list', lazy='dynamic')

    def __init__(self, name, user_id):
        self.name=name
        self.user_id = user_id

# a model of a list item for the database
# it refers to a list
class ListItem(db.Model):
    __tablename__='items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id'))  # this ought to be a "foreign key"
    completion= db.Column(db.Boolean)

    def __init__(self, name, list_id, completion):
        self.name=name
        self.list_id=list_id
        self.completion=completion


# put some data into the tables
def dbinit():
    user_list = [
        User("Ivan","123456",'totallyanemail@mail.com'), 
        User("Icen","654321",'veryreal@mail.com')
        ]
    db.session.add_all(user_list)

    # find the id of the user Ivan
    ivan_id = User.query.filter_by(username="Ivan").first().id

    all_lists = [
        List("Shopping",ivan_id), 
        List("Chores",ivan_id)
        ]
    db.session.add_all(all_lists)

    # find the ids of the lists Chores and Shopping

    chores_id = List.query.filter_by(name="Chores").first().id
    shopping_id= List.query.filter_by(name="Shopping").first().id

    all_items = [
        ListItem("Potatoes",shopping_id, False), 
        ListItem("Shampoo", shopping_id, True),
        ListItem("Wash up",chores_id, True), 
        ListItem("Vacuum bedroom",chores_id, False)
        ]
    db.session.add_all(all_items)

    # commit all the changes to the database file
    db.session.commit()