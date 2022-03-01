from flask import Flask, render_template
app = Flask(__name__)

#route to the index
@app.route('/')
def index():
    return render_template('index.html')

