from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
from bson.json_util import loads, dumps
import json

app = Flask('app')
app.config.from_pyfile('config.cfg')
mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template('home.html')


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)