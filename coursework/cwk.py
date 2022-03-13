# import SQLAlchemy
from crypt import methods
import email
from email import message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug import security
from markupsafe import escape



# create the Flask app
from flask import Flask, render_template,redirect,request,flash
app = Flask(__name__)

# select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///todo.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] ="BryanPeopleSecretKey"
safe_string = escape ("escape?")
# set up a 'model' for the data you want to store
from db_schema import Households, db, User, Bills,User_Bill, Notfications, dbinit 
from flask_login import LoginManager, login_user, current_user, logout_user, UserMixin

# init the database so it can connect with our app
db.init_app(app)

# change this to False to avoid resetting the database every time this app is restarted
resetdb = False
if resetdb:
    with app.app_context():
        # drop everything, create all the tables, then put some data into the tables
        db.drop_all()
        db.create_all()
        dbinit()

login_manager = LoginManager()
login_manager.init_app(app)

# Manages login and loads the user.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# route to the main index page
@app.route('/') 
def index():
    return render_template('index.html')

# route to the index page when logged in. returns all notfications to it so it can be displayed.
@app.route('/indexLogged',methods=['GET']) 
def indexLogged():
    notfications = Notfications.query.filter_by(user_id=current_user.id)
    return render_template('indexLogged.html',notfications=notfications)

# Handles the deletion of notfications from the logged index page.
@app.route('/indexLoggedAPI',methods=['POST']) 
def indexLoggedAPI():
    notfication_id = request.form.get('notfication_id')
    notfication = Notfications.query.filter_by(id=notfication_id).first()
    db.session.delete(notfication)
    db.session.commit()
    return redirect('/indexLogged')

# Checks if the user is logged in or not. Redirects to the appropriate page if so.
@app.route('/login', methods=['GET'])
def log():
    if current_user.is_authenticated:
        return redirect('/indexLogged')
    else:
        return render_template("login.html")

# Handles logging in the user if the username and password is correct. if not redirects them to the login page.
@app.route('/loginAPI', methods=['POST'])
def logAPI():
    name = request.form.get('username')
    password = request.form.get('password')

    # find the users with this name
    user = User.query.filter_by(username=name).first() #Might be the issue
    if user is None:
        return redirect('/')
    if not security.check_password_hash(user.password_hash, password):
        return redirect('/login')

    # good, so log in the user
    login_user(user)
    return redirect('/indexLogged')

# Handles logging out of the user
@app.route('/logout')
def logout():
    if not current_user.is_authenticated:
        return redirect('/login')
    logout_user()
    return redirect('/')

# Checks if the user is authenticated and redirects them to the login page if so. Otherwise it stays on the register page.
@app.route('/register', methods=['GET'])
def reg():
    if current_user.is_authenticated:
        return redirect('/login')

    return render_template("register.html")

# Handles the backend of registering. Storing the username, email and password. Hashes the password for safety as well.
@app.route('/registerAPI', methods=['POST'])
def regAPI():
    if current_user.is_authenticated:
        return redirect('/login')
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    username = escape(username)
    email = escape(email)

    # create a user with this name and hashed password
    password_hash=security.generate_password_hash(password)

    # Tries to add the user, if not this means the user exists and rolls back. Redirects to the login page if the addition is successful
    try:
        newuser = User(username=username, password_hash=password_hash, email=email)
        db.session.add(newuser)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        return f"could not register {exc}"
    return redirect('/login')

# Filters the houses that the user is part of so it can be shown to them
@app.route('/addHouse',methods=['GET'])
def addHouse():
    if not current_user.is_authenticated:
        return redirect('/login')
    houses = Households.query.filter_by(user_id=current_user.id)
    return render_template("addHouse.html",houses=houses)

# Adds the current user and the users in the returned form to a house with the assigned name
@app.route('/addHouseAPI',methods=['POST'])
def addHouseAPI():
    if not current_user.is_authenticated:
        return redirect('/login')
    house_name = request.form.get('house name')
    house_members = request.form.get('members')
    house_members += f",{current_user.username}"
    house_members_list = house_members.split(',')
    print(f"House name: {house_name} Members: {house_members}")
    for member in house_members_list:
        print(f"Member name: {member}")
        username_to_id = User.query.filter_by(username=member).first().id
        db.session.add(Households(username_to_id,house_name,house_members,len(house_members_list)))
        db.session.commit()
    return redirect('/indexLogged')

# Filters the bills that the user is part of and returns it
@app.route('/createBill', methods=['GET'])
def create():
    if not current_user.is_authenticated:
        return redirect('/login')
    users = User.query.all() 
    return render_template('createBill.html',users=users)

''' 
Handles the backend for creating bills. It takes in the user names of the 
people/household that the bill will be split between. If there are any users it
will add them to a string. If a household is inserted as well, it will go through 
all the household members and add them to the same string to the users. It will 
then split them to a list of users using and go through every non empty one of them
and add the bill, its notfication and the state of each user in the bill. 
It then redirects to /Bills where the user can find their new bill added if they
were in the user list or part of the household.
'''
@app.route('/createBillAPI', methods=['POST'])
def createAPI():
    if not current_user.is_authenticated:
        return redirect('/login')
    name = request.form.get('name')
    amount = request.form.get('amount')
    splittingWith_house = request.form.get("splittingWithHousehold")
    splittingWith_house_separated = splittingWith_house.split(',')
    print(f"House names: {splittingWith_house}")
    splittingWith_users = request.form.get('splittingWithUsername')
    bill = Bills.query.filter_by(name=name).first()
    for house in splittingWith_house_separated:
        users_in_house =Households.query.filter_by(name=house).first()
        print(f"House number: {users_in_house} name of house: {house} ")
        splittingWith_users +=f",{users_in_house.members}" 
    splittingWith_users_separated = splittingWith_users.split(',')
    number_of_users_to_split_with = len(splittingWith_users_separated)
    for user in splittingWith_users_separated:
        if user is not '':
            print(f"Username: {user}. Users separated: {splittingWith_users_separated} and just Users: {splittingWith_users}")
            username_to_id = User.query.filter_by(username=user).first().id
            db.session.add(Bills(name, int(amount)/number_of_users_to_split_with, username_to_id,splittingWith_users, False))
            db.session.commit()
            message = f"{current_user.username} added you to the bill '{name}' which ammounts to {amount}. You have to pay {int(amount)/number_of_users_to_split_with}"
            db.session.add(Notfications(username_to_id,message))
            db.session.commit()
            print(f"name of bill: {name} and user_name_to_id: {username_to_id}")
            bill_add = Bills.query.filter_by(name=name,user_id=username_to_id).first()
            db.session.add(User_Bill(username_to_id,bill_add.id,False))
            db.session.commit()
    return redirect('/Bills')

# Filters the bills of the current user and its state and sends it to the page to be displayed
@app.route('/Bills', methods=['GET'])
def bill():
    if not current_user.is_authenticated:
        return redirect('/login')
    users = User.query.all() # might be the issue
    bills = Bills.query.filter_by(user_id=current_user.id).all()
    user_bills = []
    for bill in bills:
        user_bills += User_Bill.query.filter_by(bill_id=bill.id).all()
    return render_template('Bills.html', users=users, bills=bills,user_bills=user_bills)
    
'''
Performs the backend of setting the bill as paid by one user and checks whether
the whole payment is pending or complete (Flase/True respectively). It does this
by getting the bill id and whether the user already paid for the bill or not by 
filtering it from the database. It sets that value as true as we are only routed 
to it if the user decides to pay the bill. It then gets everyone else in the bill
and send the notfication thst the current user paid for their part of the bill.
it then checks if all the user paid or not, if they did then it will change the
transcation to completed from pending (True/False).
'''
@app.route('/BillsAPI', methods=['POST'])
def BillsAPI():
    if not current_user.is_authenticated:
        return redirect('/login')
    
    complete = True
    bill_id = request.form.get('billToChange')
    bill = Bills.query.filter_by(id=bill_id).first()
    print(f"User_id = {current_user.id} and bill_id = {bill_id} and bill = {bill}")
    user_bill = User_Bill.query.filter_by(user_id=current_user.id,bill_id = bill_id).first()
    user_bill.user_bill_completion = True
    splittingWithUsers = request.form.get('splittingWithUsers')
    print(f"Splitting with users: {splittingWithUsers}")
    splittingWithUsers_separated = splittingWithUsers.split(',')
    print(f"Splitting with users sep: {splittingWithUsers_separated}")
    if '' in splittingWithUsers_separated:
        splittingWithUsers_separated.remove('')

    for user in splittingWithUsers_separated:
        if user != current_user.username:
            username_to_id = User.query.filter_by(username=user).first().id
            message = f"{current_user.username} paid their share for {bill.name} which ammounted to {bill.amount}. "
            db.session.add(Notfications(username_to_id,message))
            db.session.commit()

    for user in splittingWithUsers_separated:
        print(f"User: {user}")
        user_id = User.query.filter_by(username=user).first().id
        bill = Bills.query.filter_by(user_id=user_id,name=bill.name).first()
        print(f"User id {user_id} and bill id: {bill_id}")
        user_bill = User_Bill.query.filter_by(user_id=user_id,bill_id = bill.id).first()
        print(f"User bill completion: {user_bill.user_bill_completion}")
        if user_bill.user_bill_completion is False:
            print(f"Not true")
            complete = False
    for user in splittingWithUsers_separated:
        if complete:
            print(f"Bill: {bill}")
            user_id = User.query.filter_by(username=user).first().id
            bill = Bills.query.filter_by(user_id=user_id,name=bill.name).first()
            bill.completion = True
            db.session.commit()
            print(f"bill completion: {bill.completion}")
    return redirect('/Bills')
