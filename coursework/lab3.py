# import SQLAlchemy
import email
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug import security


# create the Flask app
from flask import Flask, render_template,redirect,request,flash
app = Flask(__name__)

# select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///todo.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] ="Bryan"
# set up a 'model' for the data you want to store
from db_schema import ListItem, db, User, List, dbinit 
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
    return User.query.get(int(user_id)) #Might be the issue

#route to the index
@app.route('/') 
def index():
    return render_template('index.html')

@app.route('/indexLogged') 
def indexLogged():
    return render_template('indexLogged.html')

@app.route('/login',methods=['GET'])
def log():
    if current_user.is_authenticated:
        return redirect('/toDoList')
    else:
        return render_template("login.html")

@app.route('/loginAPI',methods=['POST'])
def logAPI():
        
    name=request.form.get('username')
    password=request.form.get('password')

    # find the users with this name
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
    if current_user.is_authenticated:
        pass
    else:
        return redirect('/login')
    logout_user()
    return redirect('/')

@app.route('/register',methods=['GET'])
def reg():
    if current_user.is_authenticated:
        return redirect('/login')

    return render_template("register.html")

@app.route('/registerAPI',methods=['POST'])
def regAPI():
    if current_user.is_authenticated:
        return redirect('/login')

    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')

        password_hash=security.generate_password_hash(password)
        # create a user with this name and hashed password
        # still not secure unless using HTTPS 

        try:
            newuser = User(username=username, password_hash=password_hash, email=email)
            db.session.add(newuser)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            return "could not register "+str(exc)
        flash("registered succesfully, now log in")
        return redirect('/login')

@app.route('/createList',methods=['POST','GET'])
def create():
    if current_user.is_authenticated:
        pass
    else:
        return redirect('/login')
    if request.method == 'POST':
        name = request.form.get('name')
        db.session.add(List(name,current_user.username))
        db.session.commit()
        return redirect('/toDoList')
    return render_template('createList.html')

@app.route('/toDoList',methods=['GET','POST'])
def toDo():
    if current_user.is_authenticated:
        pass
    else:
        return redirect('/login')
    users = User.query.all() #might be the issue
    lists = List.query.filter_by(user_id = current_user.username)
    return render_template('toDoList.html', users=users,lists=lists)