from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
from flask_cors import CORS
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
import datetime
from bson.json_util import dumps
import json
#import os
app = Flask('app')
app.config.from_pyfile('config.cfg')
mongo = PyMongo(app)
CORS(app)
patch_request_class(app, 32 * 1024 * 1024)

app.config['MEME_UPLOADS'] = 'static/img'
meme_folder = UploadSet('meme', IMAGES, default_dest=lambda app: app.config['MEME_UPLOADS'])
configure_uploads(app, meme_folder)


@app.route('/')
def index():
    if 'username' in session:
        posts = mongo.db.posts
        all_docs = posts.find({})
        all_docs_string = dumps(all_docs)
        all_docs2 = json.loads(all_docs_string)
        #posts = os.listdir(app.config['MEME_UPLOADS'])
        return render_template('home.html', user=session['username'], post_data=all_docs2)
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

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
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name': request.form['username'], 'password': hashpass, 'monies': 25000})
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
        posts = mongo.db.posts
        price = request.form['price']
        try:
            price = float(price)
        except ValueError:
            return render_template('create.html', message="please enter a valid number")
        
        dot = photo.filename.index('.')
        photo_type = photo.filename[dot::]
        meme_name = request.form['memeName']
        existing_meme = posts.find_one({'memeName': meme_name+photo_type})
        if request.form['totalShares'].isnumeric():
            totalShares = int(request.form['totalShares'])
        else:
            return render_template('create.html', message="please enter a valid number of shares")
        if existing_meme is None:
            now = datetime.datetime.now()
            meme_folder.save(request.files['photo'], folder=session['username'],name=meme_name + '.')
            posts.insert_one({'owner': session['username'] ,'memeName': meme_name+photo_type, 'price': price, 
            'time': now.hour, 'bought': 0, 'sold': 0, 'regName': meme_name, 'totalShares': totalShares, 'prevBuys': 0, 'prevSells': 0})
            return redirect(url_for('index'))
        return render_template('create.html', message="meme name already exists!")
    return render_template('create.html', message="")

@app.route('/changePrice', methods=['GET', 'POST'])
def change_price():
    posts = mongo.db.posts
    all_posts = posts.find({})
    all_posts_string = dumps(all_posts)
    all_posts2 = json.loads(all_posts_string)
    return {'status': 'sucess'}

@app.route('/buy/<meme_name>', methods=['GET', 'POST'])
def buy(meme_name):
    post = mongo.db.posts    
    users = mongo.db.users
    user = users.find_one({'name': session['username']})
    post_to_update = post.find_one({'memeName': meme_name})
    dec = post_to_update['price'] * -1
    current_user = session['username']+'Portfolio'
    users_portfolio = mongo.db[current_user]
    if post_to_update['totalShares'] > 0 and user['monies'] > post_to_update['price']:
        post.update_one({'memeName': meme_name}, {'$inc': {'bought': 1, 'totalShares': -1} })
        users.update_one({'name': session['username']}, {'$inc': {'monies': dec} })
        existing_stonk = users_portfolio.find_one({'stonkInfo.stonkName': meme_name})
        if existing_stonk is None:
            users_portfolio.insert_one({'stonkInfo': {'stonkName': meme_name, 'amount': 1, 'stonkPrice': post_to_update['price']}})
        elif existing_stonk != None:
            users_portfolio.update_one({'stonkInfo.stonkName': meme_name}, {'$inc': {'stonkInfo.amount': 1}})
    elif user['monies'] < post_to_update['price']:
        updated_post = post.find_one({'memeName': meme_name})
        post_update_string = dumps(updated_post)
        post_to_update2 = json.loads(post_update_string)    
        return {'postToUpdate': post_to_update2, 'message': "you don't have enough monie to buy this!"}
    updated_post = post.find_one({'memeName': meme_name})
    post_update_string = dumps(updated_post)
    post_to_update2 = json.loads(post_update_string)
    return {'postToUpdate': post_to_update2, 'message': ''}


@app.route('/profile')
def profile():
    return render_template('profile.html', user=session['username'])


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)
