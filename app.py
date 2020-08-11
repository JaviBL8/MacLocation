from flask import Flask, request, jsonify
from pymongo import MongoClient
import json
import os
from bson import ObjectId
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, jwt_optional
)

app = Flask(__name__)

db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_KEY')

# Setup authentication
app.config['JWT_SECRET_KEY'] = os.environ.get('APP_KEY')
jwt = JWTManager(app)

# Setup database connection
client = MongoClient("mongodb+srv://" + db_user + ":" + db_password + "@macstore-rmprr.mongodb.net/test?retryWrites=true&w=majority")
db=client.AP_DB.loc

# Own JSON encoder
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

# Method to create tokens
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    if username != 'admin' or password != 'HTC-Desire':
        return jsonify({"msg": "Bad username or password"}), 401

    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

# Verify identity
@app.route('/user', methods=['GET'])
@jwt_optional
def getUser():
    current_user = get_jwt_identity()
    if current_user:
        return jsonify(logged_in_as=current_user), 200
    else:
        return jsonify(logged_in_as='anonymous user'), 200

# Get all locations
@app.route('/ap', methods=['GET'])
def getAllAP():
    return jsonify(list(db.find({}))), 200

# Get location of AP
@app.route('/ap/<mac>', methods=['GET'])
def getByMac(mac):
    ap = db.find_one({'mac': mac})
    return jsonify(ap), 200

# Create new AP
@app.route('/ap', methods=['POST'])
@jwt_required
def addAP():
    data = request.get_json()
    db.insert_one(data)
    return data, 200

# Delete AP
@app.route('/ap/<mac>', methods=['DELETE'])
@jwt_required
def removeAP(mac):
    db.delete_one({'mac': mac})    
    return jsonify({'message': 'Deleted ' + mac }), 200

# Update location for AP
@app.route('/ap', methods=['PUT'])
@jwt_required
def updateAP():
    ap = request.get_json()
    db.update({
        'mac': ap['mac']
    },{
        '$set': {
            'es': ap['es']
        }
    }, upsert=False)
    return jsonify({'message': 'Updated ' + ap['mac'] }), 200

if __name__ == '__main__':
    app.run()