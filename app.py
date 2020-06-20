from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
from bson.json_util import loads, dumps
import json
from flask_cors import CORS
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class

app = Flask('app')
app.config.from_pyfile('config.cfg')
mongo = PyMongo(app)
CORS(app)
patch_request_class(app, 32 * 1024 * 1024)

app.config['MEME_UPLOADS'] = 'static'
meme_folder = UploadSet('meme', IMAGES, default_dest=lambda app: 'static')
configure_uploads(app, meme_folder)


@app.route('/')
def index():
    if 'username' in session:
        return render_template('home.html', user=session['username'])
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        return render_template('register.html', message="This name is already taken!")

    return render_template('register.html', message="")

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST' and 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename == '':
            return render_template('create.html', message="please post a valid file")
        price = request.form['price']
        if price.isnumeric():
            price = int(price)
        else:
            return render_template('create.html', message="please enter a valid number")
        caption = request.form['caption']
        filename = meme_folder.save(request.files['photo'], folder=session['username'])
        return redirect(url_for('index'))
    return render_template('create.html', message="")

@app.route('/profile')
def profile():
    return render_template('profile.html', user=session['username'])


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)