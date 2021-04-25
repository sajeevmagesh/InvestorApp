# Web handler (Flask) import
from investors import investors
from mgmt import mgmt
from user import user
from api import api
from flask import Flask, Blueprint, render_template

# Importing OS
import os

# Initializing Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lol'
# Importing and initializing API blueprint
app.register_blueprint(api)

# Importing and initializing user blueprint
app.register_blueprint(user)

# Importing and initializing user management blueprint
app.register_blueprint(mgmt)

app.register_blueprint(investors)

app.secret_key = os.urandom(24)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error/500.html'), 500


if __name__ == '__main__':
    
    app.run()
