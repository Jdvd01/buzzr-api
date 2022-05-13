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
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.environ.get('FLASK_APP_KEY')
MIGRATE = Migrate(app, db)
jwt = JWTManager(app)
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

# Sign_up route
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


#Log_in route
@app.route('/login', methods=['POST'])
def handle_login():
    
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if email is not None and password is not None:
        user = User.query.filter_by(email=email, password=password).one_or_none()

        if user is not None:
            create_token = create_access_token(identity = user.id)
            return jsonify({
                "email": user.email,
                "token": create_token,
                "user_id": user.id
            }), 200
        else:
            return jsonify({
                "msg": "User not found"
            }), 404
    else:
        return jsonify({
            "msg": "Something is wrong, try again"
        }), 400


# Users profile
@app.route('/user/<int:user_id>', methods=['GET', 'PUT'])
@jwt_required()
def handle_user(user_id = None):

    user_id = get_jwt_identity()

    if request.method == 'GET':

        if user_id is None:
            return jsonify({
                "msg": "User not found"
            }), 404
        else:
            user = User.query.filter_by(id = user_id).first()
            if user is not None:
                return jsonify(user.serialize()), 200
            else:
                return jsonify({
                "msg": "User not found"
            }), 404

    if request.method == 'PUT':

        body = request.json

        user_update = User.query.filter_by(id = user_id).first()

        if user_update is None:
            return jsonify({
                "msg": "User not found"
            }), 404
        
        try:
            user_update.email = body["email"]
            user_update.first_name = body["first_name"]
            user_update.last_name = body["last_name"]
            user_update.username = body["username"]
            db.session.commit()
            return jsonify(user_update.serialize()), 202
        except Exception as error:
            db.session.rollback()
            return jsonify(error.args)


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
