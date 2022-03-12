# import SQLAlchemy
import email
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
from db_schema import db, User, Bills,User_Bill, dbinit 
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # Might be the issue

#route to the index
@app.route('/') 
def index():
    return render_template('index.html')

@app.route('/indexLogged') 
def indexLogged():
    return render_template('indexLogged.html')

@app.route('/login', methods=['GET'])
def log():
    if current_user.is_authenticated:
        return redirect('/toDoList')
    else:
        return render_template("login.html")

@app.route('/loginAPI', methods=['POST'])
def logAPI():
    name = request.form.get('username')
    password = request.form.get('password')

    # find the users with this name
    print(f"Name before user: {name}")
    user = User.query.filter_by(username=name).first() #Might be the issue
    print(f"HELLO: {name} {user} a {user.password_hash} a {password}")
    if user is None:
        return redirect('/')
    if not security.check_password_hash(user.password_hash, password):
        return redirect('/login')

    # good, so log in the user
    login_user(user)
    return redirect('/toDoList')

@app.route('/logout')
def logout():
    if not current_user.is_authenticated:
        return redirect('/login')
    logout_user()
    return redirect('/')

@app.route('/register', methods=['GET'])
def reg():
    if current_user.is_authenticated:
        return redirect('/login')

    return render_template("register.html")

@app.route('/registerAPI', methods=['POST'])
def regAPI():
    if current_user.is_authenticated:
        return redirect('/login')

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        username = escape(username)
        email = escape(email)

        password_hash=security.generate_password_hash(password)
        # create a user with this name and hashed password
        # still not secure unless using HTTPS 

        try:
            newuser = User(username=username, password_hash=password_hash, email=email)
            db.session.add(newuser)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return f"could not register {exc}"
        flash("registered succesfully, now log in")
        return redirect('/login')

@app.route('/createList', methods=['GET'])
def create():
    if not current_user.is_authenticated:
        return redirect('/login')
    users = User.query.all() 
    return render_template('createList.html',users=users)

@app.route('/createListAPI', methods=['POST'])
def createAPI():
    if not current_user.is_authenticated:
        return redirect('/login')
    name = request.form.get('name')
    amount = request.form.get('amount')
    splittingWith = request.form.get('splittingWithUsername')  
    splittingWith += f",{current_user.username}"
    splittingWithSeparated = splittingWith.split(',')
    bill = Bills.query.filter_by(name=name).first()
    for user in splittingWithSeparated:
        username_to_id = User.query.filter_by(username=user).first().id
        print(f"username to id {username_to_id}")
        db.session.add(Bills(name, amount, username_to_id, splittingWith, False))
        db.session.commit()
        bill_add = Bills.query.filter_by(name=name,user_id=username_to_id).first()
        db.session.add(User_Bill(username_to_id,bill_add.id,False))
        db.session.commit()
    return redirect('/toDoList')

@app.route('/toDoList', methods=['GET'])
def toDo():
    if not current_user.is_authenticated:
        return redirect('/login')
    users = User.query.all() # might be the issue
    bills = Bills.query.filter_by(user_id=current_user.id).all()
    user_bills = []
    for bill in bills:
        user_bills += User_Bill.query.filter_by(bill_id=bill.id).all()
    print(user_bills)
    return render_template('toDoList.html', users=users, bills=bills,user_bills=user_bills)
    

@app.route('/toDoListAPI', methods=['POST'])
def toDoAPI():
    if not current_user.is_authenticated:
        return redirect('/login')
    bill_id = request.form.get('billToChange')
    bill = Bills.query.filter_by(id=bill_id).first()
    user_bill = User_Bill.query.filter_by(user_id=current_user.id,bill_id = bill_id).first()
    user_bill.user_bill_completion = True
    db.session.commit()
    splittingWithUsers = request.form.get('splittingWithUsers')
    for user in splittingWithUsers.split(','):
        user_id = User.query.filter_by(username=user).first().id
        user_bill = User_Bill.query.filter_by(user_id=user_id,bill_id = bill_id).first()
        if user_bill is not True:
            return redirect('/toDoList')
    
    for user in splittingWithUsers.split(','):
        bill = Bills.query.filter_by(user_id=user,name=bill.name).first()
        print(f"Bill: {bill}")
        bill.completion = True
