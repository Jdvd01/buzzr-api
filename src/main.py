"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""

from hashlib import new
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/signup', methods = ['POST'])
def sign_up():
    body = request.json
    email = body.get("email", None)
    password = body.get("password", None)
    name = body.get("name", None)
    last_name = body.get("last_name", None)
    username = body.get("username", None)

    if email or password or name or last_name or username is not None:
        correo = User.query.filter_by(email = email).first()
        if correo is not None:
            return jsonify({
                "msg":"Email already exist"
            }), 500
        else:
            usertag = User.query.filter_by(username = username).first()
            if usertag is not None:
                return jsonify({
                    "msg":"username already in use"
                }), 500
            else:
                try:
                    new_user = User(
                        email = email,
                        password = password,
                        first_name = name,
                        last_name = last_name,
                        username = username
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    return jsonify({
                        "msg": "Usuario creado"
                    }), 201
                except Exception as error:
                    db.session.rollback()
                    return jsonify(error.args), 500
    else:
        return jsonify({
            "msg":"Something Happened"
        }), 400



# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
