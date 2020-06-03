from flask import Flask, jsonify, request
from flask_restful import Api, Resource 
from pymongo import MongoClient
from passlib.context import CryptContext
import spacy

app = Flask(__name__)
api = Api(app)
client = MongoClient('mongodb://db:27017')
db= client.SimilarityDB
users = db['Users']
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def user_exist(username):
    if users.find({'Username': username}).count() == 0:
        return False
    else:
        return True

def verify_pw(username, password):
    if not user_exist(username):
        return False
    hash_pw = users.find({
        'Username': username
        })[0]['Password']
    return pwd_context.verify(password, hash_pw)

def count_tokens(username):
    tokens = users.find({
        'Username': username
        })[0]['Tokens']
    return tokens
    

class Ping(Resource):
    def get(self):
        return jsonify('pong')

class Register(Resource):
    def post(self):
        pd = request.get_json()
        username = pd['username']
        password = pd['password']
        if user_exist(username):
            ret_json = {
                    'status': 301,
                    'msg': 'Invalid username'
                    }
            return jsonify(ret_json)

        hash_pw = pwd_context.hash(password)
        users.insert({
            'Username' : username,
            'Password' : hash_pw,
            'Tokens' : 6
            })
        ret_json = {
                'status': 200,
                'msg': "You've successfully signed up to the API"
                }
        return jsonify(ret_json)

class Detection(Resource):
    def post(self):
        pd = request.get_json()
        username = pd['username']
        password = pd['password']
        text1 = pd['text1']
        text2 = pd['text2']

        if not user_exist(username):
            ret_json = {
                    'status': 301,
                    'msg': 'Invalid username'
                    }
            return jsonify(ret_json)
        
        correct_pw = verify_pw(username, password)
        if not correct_pw:
            ret_json = {
                    'status': 302,
                    'msg': 'Invalid password'
                    }
            return jsonify(ret_json)
        
        num_tokens = count_tokens(username)
        if num_tokens <= 0:
            ret_json = {
                    'status': 303,
                    'msg': 'Out of tokens, please refill'
                    }
            return jsonify(ret_json)
        
        # todo load model
        nlp = spacy.load("en_core_web_sm") 
        text1 = nlp(text1)
        text2 = nlp(text2)
        ratio = text1.similarity(text2)
        ret_json = {
            'status': 200,
            'similarity': ratio,
            'msg': 'Similarity score calcilated successfully'
            }

        current_tokens = count_tokens(username)
        users.update({
            'Username': username
            }, {
                '$set':{
                    'Tokens': current_tokens - 1
                    }
                })
        return jsonify(ret_json)

class Refill(Resource):
    def post(self):
        pd = request.get_json()
        username = pd['username']
        admin_pw = pd['admin_pw']
        refill_amount = pd['refill']
        if not user_exist(username):
            ret_json = {
                    'status': 301,
                    'msg': 'Invalid username'
                    }
            return jsonify(ret_json)
        
        correct_pw = 'asdf' # just for learning purpose 
        if not admin_pw == correct_pw:
            ret_json = {
                    'status': 302,
                    'msg': 'Invalid password'
                    }
            return jsonify(ret_json)

        users.update({
            'Username': username
            }, {
                '$set':{
                    'Tokens': refill_amount
                    }
                })
        ret_json = {
            'status': 200,
            'msg': 'Refilled successfully'
            }
        return jsonify(ret_json)


api.add_resource(Ping, '/ping')
api.add_resource(Register, '/register')
api.add_resource(Refill, '/refill')
api.add_resource(Detection, '/detect')

if __name__ == '__main__':
    app.run(host='0.0.0.0')

