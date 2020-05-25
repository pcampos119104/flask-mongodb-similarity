from flask import Flask, jsonify
from flask_restful import Api, Resource 

app = Flask(__name__)
api = Api(app)

class Ping(Resource):
    def get(self):
        return jsonify('pong')

api.add_resource(Ping, '/ping')
