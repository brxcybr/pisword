from uuid import uuid4

# import cryptography library
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.x509 import load_pem_x509_certificate

# import flask libraries
from flask import Blueprint, request, jsonify
from flask_restful import Resource, reqparse

class Welcome(Resource):
    def get(self):
        """ Prints the welcome message at launch """
        msg = "Welcome to Pi|SWORD - The World's most lightweight Security Orchestration and Response Framework\n"
        return msg

class Login(Resource):
    def post(self):
        # Create a request parser to validate and extract login details from the POST request body
        self.req_parser = reqparse.RequestParser()
        self.req_parser.add_argument('username', type=str, required=True, help='Username is required')
        self.req_parser.add_argument('password', type=str, required=True, help='Password is required')
        
        # Parse the request
        args = self.req_parser.parse_args()
        username = args['username']
        password = args['password']
        
        # TODO: Validate the username and password against a user store.
        # For this example, let's assume a simple check where the username is "admin" and password is "password"
        if username == "admin" and password == "password":
            session_token = str(uuid4())  # Generate a random UUID for the session token
            return {"message": "Login successful", "session_token": session_token}, 200
        else:
            return {"message": "Login failed", "session_token": None}, 401

class ExecutePlaybook(Resource):
    def run(self, playbook):
        pass

class StopPlaybook(Resource):
    def stop(self, playbook):
        pass

class CreatePlaybook(Resource):
    def __init__(self):
        # Create a request parser to validate and extract "name" from the POST request body
        self.req_parser = reqparse.RequestParser()
        self.req_parser.add_argument('name', type=str, required=True, help='Name for the playbook is required')
    

    def post(self):
        # Parse the request
        args = self.req_parser.parse_args()
        playbook_name = args['name']

        # Create a Playbook instance using the provided name
        playbook = playbook_name  # Assuming Playbook class initialization accepts no arguments

        # TODO: Here, you'll have logic to add the playbook to a storage system, or to set its parameters, etc.
        # For the sake of example, let's say you have a method to save it:
        # success = playbook.create_new_playbook(playbook_name)
        # if success:
        #     return {"message": f"Playbook {playbook_name} created successfully."}, 201
        # else:
        #     return {"message": f"Error creating playbook {playbook_name}."}, 500

        return {"message": f"Playbook {playbook_name} created."}, 201

class RemovePlaybook(Resource):
    def delete(self, playbook):
        pass

class ListPlaybooks(Resource):
    def list(self):
        pass

class Configure(Resource):
    def create(self, playbook):
        pass

class Status(Resource):
    def get_status(self, playbook):
        pass

class Logout(Resource):
    def post(self):
        # For simplicity, let's assume the session token is sent as a bearer token in the Authorization header
        auth_header = request.headers.get('Authorization')
        session_token = auth_header.split()[1] if auth_header else None
        
        # TODO: Invalidate the session token in the user store.
        
        return {"message": "Logged out successfully"}, 200
