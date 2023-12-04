#!/usr/bin/env python3

"""
- Author: brx.cybr@gmail.com
- Title: pySOAR
- Description: The program is a SOAR (Security Orchestration, Automation, and Response) application that is 
purpose-built to run efficiently in Edge environments, such as on a Raspberry Pi, but can run as a container
on any Linux system or virtual machine. The application reads YAML configuration files from the `./config` 
directory, and then executes the actions specified in the YAML files. The application is designed to be run 
as a container, and will run continuously until stopped. It is designed to run statelessly, meaning that it 
does not need to store any data between runs.

- Proof of Concept Feaures:
    - The application will read a YAML file from the `./config` directory, and then execute the actions
    - The application will extract threat intelligence blacklist IP data using PyMISP
    - The application will interact with the remote APIs (integrations) as specified in the config files 
    - The application will log all actions and results to a log file
- TODO:
    - Finish api_endpoints.py
    - Finish Menu().launch_playbook_menu()
    - Finish Menu().stop_playbook_menu()
    - Finish Menu().remove_playbook_menu()
    - Finish PlaybookFlowchart() class
    - Add help menu
"""

import os
from classes import Log
from menu import Menu
import curses
import traceback
import argparse

# Initialize the logger
log = Log.get_instance()
log.info("Application is starting...")

# Set server name 
SERVER_NAME = 'pysoar-dev.local' # Set this to the hostname of the server
  
# FOR USE IN FUTURE API IMPLEMENTATION
'''  
from api_endpoints import Welcome, Login, ListPlaybooks, CreatePlaybook, ExecutePlaybook, StopPlaybook, RemovePlaybook, Configure, Status, Logout
from flask import Flask, request, jsonify
from flask_restful import Api, Resource

# Initialize the API and add in the different classes to the API
# Create the Flask app and API
pysoar = Flask(__name__)
api = Api(pysoar)

api.add_resource(Welcome, '/')
api.add_resource(Login, '/login')
api.add_resource(ListPlaybooks, '/list')
api.add_resource(CreatePlaybook, '/create')
api.add_resource(ExecutePlaybook, '/execute')
api.add_resource(StopPlaybook, '/stop')
api.add_resource(RemovePlaybook, '/remove')
api.add_resource(Configure, '/configure')
api.add_resource(Status, '/status')
api.add_resource(Logout, '/logout')
'''

def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="""
        The program is a SOAR (Security Orchestration, Automation, and Response) application that is 
        purpose-built to run efficiently in Edge environments, such as on a Raspberry Pi, but can run as a container
        on any Linux system or virtual machine. The application reads YAML configuration files from the `./config` 
        directory, and then executes the actions specified in the YAML files. The application is designed to be run 
        as a container, and will run continuously until stopped. It is designed to run statelessly, meaning that it 
        does not need to store any data between runs.""",
        epilog="""Example Usage:\n\tpython3 pysoar.py\n\n""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    return parser.parse_args()

def main(stdscr):
    # Set paths for the server certificate and key
    try:
        context = (os.path.join(os.getcwd(), 'certs', SERVER_NAME + '.crt'),
               os.path.join(os.getcwd(), 'certs', SERVER_NAME + '.key'))
        # Run the server with secure communications channel
        #pysoar.run(debug=False, ssl_context=context, port=6727)
    except Exception as e:
        log.error(f"Could not initialize API context: {e}")
        pass
    """
        # Authenticate the user by calling login.
        If the login is successful, provide the following options to the user
            1. List Playbooks
            2. Create Playbook
            3. Execute Playbook
            4. Stop Playbook
            5. Remove Playbook
            6. Configure
            7. Logout

        The options will be the indices as shown above. For example, if user
        enters 1, it must invoke the 'List playbooks' function. Appropriate functions
        should be invoked depending on the user input. Users should be able to
        perform these actions in a loop until they logout. This mapping should
        be maintained in your implementation for the options.
    """
    
    # FOR FUTURE USE
    '''
    # Initialize server variables to keep track of progress
    server_message = 'UNKNOWN'
    server_status = 'UNKNOWN'
    session_token = 'UNKNOWN'
    is_login = False
    

    login_return = Login()

    server_message = login_return['message']
    server_status = login_return['status']
    session_token = login_return['session_token']
    
    print("\nThis is the server response:")
    print(server_message)
    print(server_status)
    print(session_token)

    if server_status == 200:
        is_login = True
    '''
    # Initialize the application and return the configuration manager
    try:
    # When the application is launched, initiate the menu and pass the configuration manager)
        Menu().run(stdscr)
    except Exception as e:
        log.error(f"An error occurred in [Function or Part]: {e}")
        print(f"An error occurred in [Function or Part]: {e}")
        log.error(f"An error occurred: {e}\n{traceback.format_exc()}")
        print(f"An error occurred: {e}\n{traceback.format_exc()}")
        
    except KeyboardInterrupt:
            print('\nExiting...')
            exit(0)
            
if __name__ == '__main__':
    args = parse_arguments()
    curses.wrapper(main)
