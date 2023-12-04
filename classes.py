import yaml
import os
from integrations import *
import logging
from logging.handlers import RotatingFileHandler
import pyflowchart as pfc
import requests
from importlib import import_module
from urllib3.exceptions import InsecureRequestWarning
import traceback
import time
# Globally disable SSL warnings (for self-signed certs)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ConfigurationManager:
    """This class is used to manage the configuration of all different functions the application."""
    CONFIG_PATH ='./config'

    def __init__(self):
        self._integration_mgr = None
        self._playbook_mgr = None
        self._integration_mgr = None
        # These are set to None to indicate they are not initialized yet
        self.misp = None
        self._initialized_integrations = {}
        self._enabled_integrations = None
        self._enabled_integrations_list = None
        self._enabled_playbooks = None
        self._enabled_functions = None
        self._enabled_playbook_functions = None
        self._enabled_feeds = None
        self._integrations_list = None
        self._enabled_playbooks_by_integration = None
        self._enabled_playbook_functions_by_integration = None
        self._running_playbooks = None
        self.log = Log.get_instance()
        
    def initialize_misp(self):
        # Store the passed-in MISP object as a MISPFunction object
        try:
            
            if self._integration_mgr is None:
                self._integration_mgr = self.integration_mgr  # Ensure the Integration Manager is instantiated
            if self.misp is None:  # Only create a new MISP object if it is None
                self.misp = self._integration_mgr.initialize_integration('misp')
            return self.misp
        except Exception as e:
            self.log.error(f"Error initializing MISP: {e}")
            self.log.error(f"An error occurred: {e}\n{traceback.format_exc()}")
            raise Exception(f"Error initializing MISP: {e}")

    def update_enabled_items(self):
        self._enabled_integrations = self.integration_mgr.get_enabled_integrations()
        self._enabled_playbooks = self.playbook_mgr.list_enabled_playbooks()
        self._enabled_playbook_functions = self._get_enabled_playbook_functions()
        # Now we make sure to initialize MISP if it's not already before fetching feeds
        if self.misp is None:
            self.misp = self.initialize_misp()
        self._enabled_feeds = self.misp.get_enabled_feeds()
    
    def resolve_function(self, function_name):
        """Returns a function object for the given function name."""
        try:
            # Determine which integration the function is from 
            integration_name = [integration.name for integration in self.enabled_integrations if function_name in integration.playbook_functions][0]
            module = import_module(f"integrations.{integration_name}_functions")
            class_name = function_name.capitalize() + 'Function'
            cls = getattr(module, class_name)
            return cls
        except ImportError as e:
            raise Exception(f"Could not import the specified module: {e}")
    
    # IntegrationManager Calls
    def _add_integration(self, integration_name):
        # Calls the IntegrationManager's add_integration method
        # Check if MISP Object is enabled
        if not self.misp:
            self.log.error("MISP is not initialized.")
            return
        msg, functions_to_enable = self.integration_mgr.add_integration(
            integration_name,
            self.misp,
            self.enabled_feeds,
            self.enabled_playbook_functions,
            )
        if functions_to_enable:
            for function in functions_to_enable:
                self._enable_playbook_function(function)
            self.update_enabled_items()
        self.log.warning(msg)

    def _remove_integration(self, integration_name):
        # Check if the integration exists in the enabled_playbooks dictionary
        if integration_name in self._enabled_playbooks:
            for playbook in self._enabled_playbooks[integration_name]:
                try:
                    self._disable_playbook(playbook)
                except Exception as e:
                    self.log.error(f"Error disabling playbook {playbook}: {e}")
                    return 
            # Only after successful removal, call the IntegrationManager to remove the integration
            self.integration_mgr.remove_integration(
                integration_name, 
                self.misp, 
                self.enabled_feeds, 
                self.enabled_playbook_functions, 
                self.enabled_playbooks
            )
            self.update_enabled_items()
            self.log.info(f"The {integration_name} integration has been successfully removed.")

    def _initialize_integration(self, integration_name):
            """
            Initializes an integration with the given name if it has not already been initialized,
            and returns the initialized integration.

            Args:
                integration_name (str): The name of the integration to initialize.

            Returns:
                The initialized integration.
            """
            if integration_name not in self._initialized_integrations:
                integration = IntegrationManager().initialize_integration(integration_name)
                self._initialized_integrations[integration_name] = integration
            return self._initialized_integrations[integration_name]

    def _initialize_enabled_feeds(self):
        # Initialize the MISP object and get the enabled feeds
        if self.misp is None:
            self.misp = self.initialize_misp()
        self._enabled_feeds = self.misp.get_enabled_feeds()

    def _update_integration(self, integration_name):
        # Calls the IntegrationManager's update_integration method
        msg, functions = self.integration_mgr.update_integration(integration_name, self.misp)
        for function in functions:
            self._enable_playbook_function(function)
        self.update_enabled_items()
        self.log.info(msg)

    def get_data_dependencies_by_function(self, function_name):
        """Returns a list of data dependencies for the given integration function"""
        # Figure out the integration by the function name and return the accepts data type
        # Get integration object
        integration_name = [integration.name for integration in self.enabled_integrations if function_name in integration.playbook_functions][0]
        integration_obj = [integration for integration in self.enabled_integrations if integration.name == integration_name][0]
        return integration_obj.accepts
    
    def get_unique_integration_dependencies_by_function_list(self, function_list):
        # Returns a list of unique integration dependencies for the given function list
        # Iterate over the list of functions and get the integration dependencies for each
        if 'halt_playbook' in function_list: # Remove 'halt_playbook' from function_list if it exists
            function_list.remove('halt_playbook')
        integration_dependencies = []
        for function in function_list:
            integration_name = [integration.name for integration in self.enabled_integrations if function in integration.playbook_functions][0]
            if integration_name not in integration_dependencies:
                integration_dependencies.append(integration_name)
        # Return a list of unique integration dependencies
        return list(set(integration_dependencies))
  
    # Private functions
    def _get_enabled_playbook_functions(self):
        # Return a list of enabled playbook functions if the integrations are enabled
        enabled_functions = {}
        for integration in self.enabled_integrations:
            for function in integration.playbook_functions:
                enabled_functions[function] = True
        return enabled_functions
        
    def _enable_playbook_function(self, function):
        self._enabled_playbook_functions[function] = True

    def _disable_playbook(self, playbook_name, force_stop=False):
        playbook = Playbook(playbook_name)
        if playbook.is_running():
            if force_stop:
                playbook.stop()
            else:
                self.log.error(f"Cannot disable playbook {playbook_name} while it is running. Please stop the playbook and try again.")
                return  # Exiting the method since we cannot disable a running playbook without force_stop
        # The condition to check if the playbook is in the list has been moved down to after we have possibly stopped it
        if playbook_name in self._enabled_playbooks:
            del self._enabled_playbooks[playbook_name]
            self.log.info(f"Playbook {playbook_name} has been disabled.")
        else:
            self.log.error(f"No enabled playbook found with the name: {playbook_name}")

    def _scan_configs(self):
        # Fixed the slice to correctly remove the file extension
        return [file[:-5] for file in os.listdir(self.CONFIG_PATH) if file.endswith('.yaml')]

    # Helper functions    
    @property 
    def integration_mgr(self):
        if not self._integration_mgr:
            self._integration_mgr = IntegrationManager() 
        return self._integration_mgr

    @property
    def playbook_mgr(self):
        if not self._playbook_mgr:
            self._playbook_mgr = PlaybookManager()
        return self._playbook_mgr
    
    @property
    def enabled_feeds(self):
        if self._enabled_feeds is None:
            self._initialize_enabled_feeds()
        return self._enabled_feeds
    
    @property
    def enabled_playbooks(self):
        if self._enabled_playbooks is None:
            self._enabled_playbooks = {}
        return self._enabled_playbooks
    
    @property
    def enabled_playbook_functions(self):
        if self._enabled_playbook_functions is None:
            self._enabled_playbook_functions = self._get_enabled_playbook_functions()
        return self._enabled_playbook_functions

    @property
    def enabled_playbook_functions_by_integration(self):
        """Get a dictionary of enabled playbook functions by integration name."""
        if self._enabled_playbook_functions_by_integration is None:
            self._enabled_playbook_functions_by_integration = {}
            for integration in self.enabled_integrations:
                self._enabled_playbook_functions_by_integration[integration.name] = [
                    function for function in integration.playbook_functions
                    if function in self.enabled_playbook_functions
                ]
        return self._enabled_playbook_functions_by_integration
    
    @property
    def running_playbooks(self):
        if self._running_playbooks is None:
            self._running_playbooks = self.playbook_mgr.list_running_playbooks()
        return self._running_playbooks

    @property
    def enabled_integrations(self):
        if self._enabled_integrations is None:
            self._enabled_integrations = self.integration_mgr.get_enabled_integrations()
        return self._enabled_integrations
    
    @property
    def enabled_integrations_list(self):
        # Fixed the typo in the variable name
        if self._enabled_integrations_list is None:
            self._enabled_integrations_list = [integration.name for integration in self.enabled_integrations]
        return self._enabled_integrations_list
    
    @property
    def integrations_list(self):
        if self._integrations_list is None:
            self._integrations_list = self.integration_mgr.integrations_list
        return self._integrations_list
    
    @property
    def disabled_integrations(self):
        # Fixed the logic to correctly get the list of disabled integrations
        return [integration for integration in self.integrations_list if integration not in self.enabled_integrations_list]

class Integration:
    """This class is used to manage integrations in the Integration class"""
    CONFIG_PATH = './config'
    def __init__(self, integration_name):
        self._name = integration_name
        self.log = Log.get_instance()
        self._config_path = os.path.join(self.CONFIG_PATH, self._name + '.yaml')
        # Check if the integration exists
        if not self.exists:
            self.log.error(f"Integration {self._name} does not exist.")
            raise ValueError('Integration does not exist')
        # Read in the config file and store data in a dictionary
        self._params = self._read_config()
        self._initialize_params()
        
        self._enabled = self._params[self._name]['enabled']
        self._url = self._params[self._name]['url']
        self._api_key = self._params[self._name]['api_key']
        self._ssl = self._params[self._name]['ssl']
        self._verifycert = self._params[self._name]['verifycert']
        self._accepts = self._params[self._name]['accepts']
        self._returns = self._params[self._name]['returns']
        self._playbook_functions = self._params[self._name]['playbook_functions']
    
    def _initialize_params(self):
        try:
            integration_config = self._params.get(self._name, {})
            self._enabled = integration_config.get('enabled', False)
            self._url = integration_config.get('url', '')
            self._api_key = integration_config.get('api_key', '')
            self._ssl = integration_config.get('ssl', True)
            self._verifycert = integration_config.get('verifycert', True)
            self._accepts = integration_config.get('accepts', '')
            self._returns = integration_config.get('returns', '')
            self._playbook_functions = integration_config.get('playbook_functions', [])
        except Exception as e:
            self.log.error(f"Error initializing parameters for {self._name}: {e}")
            pass
        
    def update(self):
        """Updates an integration's parameters (self._params) in memory and sends it to Integration Manager"""
        self._params[self._name]['enabled'] = self._enabled
        self._params[self._name]['url'] = self._url
        self._params[self._name]['api_key'] = self._api_key
        self._params[self._name]['ssl'] = self._ssl
        self._params[self._name]['verifycert'] = self._verifycert
        self._params[self._name]['accepts'] = self._accepts
        self._params[self._name]['returns'] = self._returns
        self._params[self._name]['playbook_functions'] = self._playbook_functions        
        # Send the updated parameters to the Integration Manager
        self.integration_mgr.update_integration(self._name, self._params)
        self.log.info(f"Integration {self._name} has been updated.")
        
    def _pack_data(self):
        """Serialize the data into a dictionary."""
        return {
            'enabled': self._enabled,
            'url': self._url,
            'api_key': self._api_key,
            'ssl': self._ssl,
            'verifycert': self._verifycert,
            'accepts': self._accepts,
            'returns': self._returns,
            'playbook_functions': self._playbook_functions
        }

    # Private functions
    def _read_config(self):
        try:
            with open(self._config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.log.error(f"Configuration file for {self._name} not found.")
            raise FileNotFoundError(f"Configuration file for {self._name} not found.")
        except Exception as e:
            self.log.error(f"Error reading configuration for {self._name}: {e}")
            raise Exception(f"Error reading configuration for {self._name}: {e}")

    # Helper functions
    @property
    def exists(self):
        return os.path.isfile(self._config_path)
    
    @property
    def name(self):
        return self._name
    
    @property
    def config_path(self):
        return self._config_path
    
    @property
    def params(self):
        return self._params
    
    @property
    def enabled(self):
        return self._enabled

    @property
    def url(self):
        return self._url
    
    @property
    def api_key(self):
        return self._api_key

    @property
    def ssl(self):
        return self._ssl
    
    @property
    def verifycert(self):
        return self._verifycert
    
    @property
    def accepts(self):
        return self._accepts
    
    @property
    def returns(self):
        return self._returns
    
    @property
    def playbook_functions(self):
        return self._playbook_functions
    
    # Setter functions
    @enabled.setter
    def enabled(self, value):  # We expect a value to be passed here
        if isinstance(value, bool):  # Check if the provided value is a boolean
            self._enabled = value  # Directly set the value of _enabled to the provided boolean
        else:
            self.log.error("'Enabled' fields must be a boolean value")
            raise ValueError("Enabled must be a boolean value")

    @url.setter
    def url(self, url):
        if isinstance(url, str):  # Check if the url is a string
            self._url = url
        else:
            self.log.error("'URL' field must be a string")
            raise TypeError('URL must be a string')

    @api_key.setter
    def api_key(self, api_key):
        if isinstance(api_key, str):
            if len(api_key) <= 128:  # API Key length check
                self._api_key = api_key
            else: 
                raise ValueError('API Key must be less than 128 characters')
        else:
            raise TypeError('API Key must be a string')

    @ssl.setter
    def ssl(self, value):
        if isinstance(value, bool):  # Check if the value is a boolean
            self._ssl = value  # Set the SSL value based on the provided boolean
        else:
            raise ValueError("SSL must be a boolean value")

    @verifycert.setter
    def verifycert(self, value):
        if isinstance(value, bool):  # Check if the value is a boolean
            self._verifycert = value  # Set the verifycert value based on the provided boolean
        else:
            self.log.error("'Verifycert' field must be a boolean value")
            raise ValueError("Verifycert must be a boolean value")

class IntegrationManager:
    CONFIG_PATH ='./config'
    """This class is used to manage integrations in the Integration class"""
    def __init__(self):
        self._integrations_list = []
        self._enabled_integrations = []
        # Store the passed-in integration objects
        self._integration_class_cache = {}
        self.log = Log.get_instance()
    
    def get_enabled_integrations(self):
        enabled_integrations = []
        errors = []
        # Iterate over the YAML files in the `./config` directory
        for integration_name in self.scan_integrations():
            try:
                integration = Integration(integration_name)
                if integration.enabled:
                    enabled_integrations.append(integration)
            except Exception as e:
                errors.append(f"Error initializing integration: {e}")
        if errors:
            for error in errors:
                self.log.error(error)
        # Return the list of enabled integrations
        return enabled_integrations
    
    def initialize_integration(self, integration_name):
        # Check if we have already initialized this integration and return it from the cache
        if integration_name in self._integration_class_cache:
            return self._integration_class_cache[integration_name]

        try:
            module = import_module(f"integrations.{integration_name}_functions")
            class_name = integration_name.capitalize() + 'Function'
            cls = getattr(module, class_name)
            # ... rest of the method ...
        except ImportError as e:
            raise Exception(f"Could not import the specified module: {e}")
        
        # Check if the integration is enabled
        integration_obj = self._get_integration_obj_by_name(integration_name)
        if integration_obj or Integration(integration_name).exists:
            # Store in cache only if it's a newly initialized enabled integration
            if integration_obj:
                self._integration_class_cache[integration_name] = cls(integration_obj)
            else:
                integration_obj = Integration(integration_name)  # Don't cache if not enabled
            return cls(integration_obj)
        
        # Raise an error if the integration does not exist
        raise Exception(f"Integration {integration_name} does not exist.")
    
    def add_integration(self, integration_name, misp_obj, feeds, functions):
        # You would typically call the necessary functions or methods here to add the integration
        self.log.info(f"Adding {integration_name} integration...")

        # Check if integration is already enabled
        if self._get_integration_obj_by_name(integration_name):
            return (f"{integration_name} is already enabled. Returning..."), []
        try:
            # Create an integration object to read the configuration
            integration_obj = Integration(integration_name)
            
            # Ensure the MISP feeds for the accepted data types are enabled
            self._enable_feeds_for_integration(misp_obj, integration_obj)
            # update the integration's enabled status in the enabled_integrations dictionary
            self._enabled_integrations.append(integration_obj)
            
            # Notify the user which feeds and playbook functions have been enabled
            enabled_feeds = ', '.join([feed for feed, details in feeds.items() if feed in misp_obj.FEEDS_BY_DATA_TYPE[integration_obj.name]])
            enabled_functions = ', '.join([function for function in functions if function in integration_obj.playbook_functions])
            msg = self._generate_success_message(integration_name, integration_obj, enabled_feeds, enabled_functions)
            return msg
        except Exception as e:
            self.log.error(f"Failed to add {integration_name} integration: {e}")

    def remove_integration(self, integration_name, misp_obj, feeds, functions, playbooks, force_removal=False):
        # Implementation for removing an integration
        warning = self._generate_removal_warning(integration_name, feeds[integration_name]['data_types'], functions[integration_name], playbooks[integration_name])
        
        # The confirmation now comes as a parameter, `force_removal`
        self.confirm_removal(integration_name, misp_obj, feeds, functions, force_removal)

    def _perform_removal(self, integration_name, misp_obj, feeds, functions): 
        # 1. Disable MISP feeds
        for data_type, details in list(feeds.items()):  # Use list to create a copy for safe iteration
            if integration_name in details['integrations']:  # Assuming that 'integrations' is a list of integration names associated with the feed
                if len(details['integrations']) == 1:  # This is the only integration using the feed
                    feed_id = details['feed_id']
                    misp_obj.disable_threat_feed(feed_id)
                    del feeds[data_type]  # Remove the feed from the dictionary
                else:
                    details['integrations'].remove(integration_name)  # Remove this integration from the feed's list

        # 2. Remove from enabled_integrations
        self._enabled_integrations = [
            integration for integration in self._enabled_integrations
            if integration.name != integration_name
        ]

        # 3. Disable playbook functions
        for function in list(functions[integration_name]):
            del functions[function]

        return feeds, functions
    
    def confirm_removal(self, integration_name, misp_obj, feeds, functions, force_removal=False):
        if force_removal:
            self._perform_removal(integration_name, misp_obj, feeds, functions)
            self.log.info(f"{integration_name} integration has been removed.")
        else:
            self.log.info("Removal cancelled.")

    def update_integration(self, integration_name, misp_obj):
        self.log.info(f"Reloading {integration_name} integration...")

        integration_obj = self._get_integration_obj_by_name(integration_name)
        if not integration_obj:
            self.log.info(f"Integration {integration_name} not found among enabled integrations. Adding it first.")
            self.add_integration(integration_name, misp_obj)
            integration_obj = self._get_integration_obj_by_name(integration_name)
            
        # Ensure the MISP feeds for the accepted data types are enabled
        self._enable_feeds_for_integration(misp_obj, integration_obj)
        self.log.info(f"{integration_name} integration has been updated with current feeds and configurations.")
        
        # Notify the user which feeds and playbook functions have been enabled
        self.log.info(f"Succesfully updated the {integration_name} integration.")
        return integration_obj.playbook_functions
            
    def scan_integrations(self):
        # Scans the integrations directory and returns a list of integration names
        return [file.split('.')[0] for file in os.listdir(self.CONFIG_PATH) if file.endswith('.yaml')]

    def save(self, integration_obj):
        """Saves all an integration object to disk in the correct format"""
        # Ensure that integration object data is updated 
        integration_obj.update()
        # Format into yaml
        config = {
            integration_obj.name: {
                integration_obj._pack_data()
            }
        }
        # Write the file to disk
        try:
            with open(integration_obj.config_path, 'w') as f:
                yaml.safe_dump(config, f)
            self.log.info(f"Integration {integration_obj.name} saved.")
        except Exception as e:
            self.log.error(f"Integration {integration_obj.name} could not be saved: {e}.")
            self.log.error(f"An error occurred: {e}\n{traceback.format_exc()}")

    def create_default_config(self, integration_name):
        try:
            # Placeholder function to create a default config for an integration.
            default_config = {
                integration_name: {
                    'enabled': True,
                    'url': '',
                    'api_key': '',
                    'ssl': True,
                    'verifycert': True,
                    'accepts': 'application/json',
                    'returns': 'application/json',
                    'playbook_functions': []
                }
            }
            config_path = os.path.join(self.CONFIG_PATH, integration_name + '.yaml')
            with open(config_path, 'w') as f:
                yaml.safe_dump(default_config, f)
            self.log.info(f"Default configuration for '{integration_name}' created.")
        except IOError as e:
            self.log.error(f"IOError when creating default configuration for '{integration_name}': {e}")
        except Exception as e:
            self.log.error(f"Unexpected error when creating default configuration for '{integration_name}': {e}")
        self.log.info(f"Default configuration for '{integration_name}' created.")

    def _get_integration_obj_by_name(self, integration_name):
        # Implementation for getting an integration object by its name
        for integration in self._enabled_integrations:
            if integration.name == integration_name:
                return integration
        return None

    def _enable_feeds_for_integration(self, misp_obj, integration_obj):
        for data_type in integration_obj.accepts:
            misp_obj.ensure_feed_enabled(data_type)

    def _generate_removal_warning(self, integration_name, feeds_to_remove, functions_to_remove, playbooks_to_remove):
        warning = f"WARNING: Removing the '{integration_name}' integration will disable the following:\n" 
        warning += f"MISP FEEDS:\n\t{', '.join(feeds_to_remove)}"
        warning += f"\nPLAYBOOK FUNCTIONS:\n\t{', '.join(functions_to_remove)}"
        warning += f"\nPLAYBOOKS:\n\t{', '.join(playbooks_to_remove)}"
        warning += "\nAre you sure you want to remove this integration? (y/n): "
        return warning

    def _generate_success_message(self, integration_obj, feeds, functions):
        success_msg = f"The {integration_obj.name} integration has been successfully added. The following features are now enabled:\n"
        success_msg += f"MISP FEEDS:\n\t{', '.join(feeds)}"
        success_msg += f"PLAYBOOK FUNCTIONS:\n\t{', '.join(functions)}\n"
        return success_msg

    @property
    def enabled_integrations(self):
        if not self._enabled_integrations:
            self._enabled_integrations = self.get_enabled_integrations()
        return self._enabled_integrations  # Ensure that the list is returned

    @property
    def integrations_list(self):
        if not self._integrations_list:
            self._integrations_list = self.scan_integrations()
        return self._integrations_list  # Ensure that the list is returned

class PlaybookManager:
    """This class is used to manage playbooks in the Playbook class"""
    PLAYBOOK_DIR = './playbooks'
    def __init__(self):
        self.playbooks_data = {}
        self._playbook_names = []
        self.log = Log.get_instance()
    
    def list_enabled_playbooks(self):
        """List all enabled playbooks based on criteria."""
        self._load_all_playbooks_if_required()

        return [playbook_name for playbook_name in self.playbooks_data.keys() 
            if self.playbooks_data[playbook_name].get('enabled')]
        
    def list_running_playbooks(self):
        """List all running playbooks."""
        # Iterate through the playbook objects and find which ones have the is_running flag set to True
        return [playbook_name for playbook_name in self.playbooks_data.keys()
            if self.playbooks_data[playbook_name].get('is_running')]
        
    def launch_playbook(self, playbook_name, config_mgr):
        """Executes logic to run the playbook"""
        # Check to ensure that the playbook exists
        if playbook_name not in self.playbooks_data:
            self.log.error(f"Playbook {playbook_name} does not exist.")
            return
        # Check if the playbook is already running
        if self.playbooks_data[playbook_name].get('is_running'):
            self.log.error(f"Playbook {playbook_name} is already running.")
            return
        # Check if the playbook is enabled
        if not self.playbooks_data[playbook_name].get('enabled'):
            self.log.error(f"Playbook {playbook_name} is not enabled.")
            return
        # Check if the playbook has any logic
        if not self.playbooks_data[playbook_name].get('logic'):
            self.log.error(f"Playbook {playbook_name} has no logic.")
            return
        # Check if the playbook has any integration dependencies
        if not self.playbooks_data[playbook_name].get('integration_dependencies'):
            self.log.error(f"Playbook {playbook_name} has no integration dependencies.")
            return
        # Check if the playbook has any functions
        if not self.playbooks_data[playbook_name].get('functions'):
            self.log.error(f"Playbook {playbook_name} has no functions.")
            return
        # Get the formatted playbook object logic 
        playbook = Playbook(playbook_name)
        # Initialize a shared_data object to store data between steps
        # Check to see if first function has any data dependencies (it shouldn't)
        if playbook.logic[0].data_dependencies:
            raise Exception(f"The first function in the {playbook.name} playbook should not have any data dependencies.")
        # Keep track of how many functions executed
        iteration = 0
        shared_data = None
        current_function = playbook.logic[iteration] # Set the current function to the first function in the playbook
        playbook.is_running = True
        try:
            while current_function.name != "halt_playbook":
                self.log.debug(f"Executing function {current_function.name} in playbook {playbook.name} with input data {shared_data}.")
                # Execute function, and retrieve the result and next function name
                shared_data, next_function_name  = current_function.execute(shared_data, config_mgr)
                # Update count of iterations
                iteration += 1
                # Log results
                self.log.debug("Function {current_function.name} executed and returned data: {shared_data}\
                    \n{current_function.name} called {next_function_name} as the next function.")
                # Find the next function object
                current_function = next((func for func in playbook.logic if func.name == next_function_name), None)
                if not current_function:
                    raise Exception(f"Function {current_function.name} does not exist.")
                iteration += 1
        except:
            playbook.is_running = False
            raise Exception(f"Error running playbook {playbook.name}.")
        # This means the playbook executed successfully or encountered a halt_playbook function
        finally:
            playbook.is_running = False
        self.log.info(f"Playbook {playbook.name} has finished executing after {iteration} iterations.")
        self.log.debug(f"Playbook {playbook.name} final shared data: {shared_data}")
        return
    
    def update_playbook_data(self, playbook_name, updates):
        """Update in-memory playbook data."""
        if self.playbooks_data.get(playbook_name):
            self.log.info(f"Updating cache for playbook {playbook_name}.")
            self.playbooks_data[playbook_name] = updates
        else:
            self.log.info(f"Adding new playbook {playbook_name} to cache.")
            self.playbooks_data[playbook_name] = updates

    def _scan_playbooks(self):
        """Returns a list of playbook filenames in the './playbooks' directory."""
        try:
            return [f for f in os.listdir(self.PLAYBOOK_DIR) 
                    if os.path.isfile(os.path.join(self.PLAYBOOK_DIR, f)) and f.endswith('.yaml') and f != 'playbook_template.yaml']
        except FileNotFoundError:
            self.log.error("Playbooks directory not found. Please create a playbooks directory and try again.")
            return []
    
    def _load_all_playbooks_if_required(self):
        """Load data from all playbooks into self.playbooks_data if not loaded."""
        if not self.playbooks_data:
            try:
                for playbook_file in self._scan_playbooks():
                    playbook_name = os.path.splitext(playbook_file)[0]  # remove the .yaml extension
                    playbook = Playbook(playbook_name)
                    self.playbooks_data[playbook_name] = playbook.data
            except Exception as e:
                self.log.error(f"Error loading playbooks: {e}")
                self.log.error(f"An error occurred: {e}\n{traceback.format_exc()}")
    
    def _disable_playbook(self, name):
        """
        Disable a playbook by setting its 'enabled' key to False.
        """
        playbook = self.playbooks_data.get(name, {}).get('Playbook', {})
        if playbook and playbook.get('enabled'):
            playbook['enabled'] = False
            self.update_playbook_data(name, playbook)
            self.log.info(f"Playbook {name} has been disabled.")
        else:
            self.log.info(f"Playbook {name} is already disabled or does not exist.")

    def _delete_playbook(self, name):
        """
        Delete a playbook's YAML file after seeking user confirmation.
        NOTE: Ensure any references to the playbook elsewhere are also cleaned up.
        """
        filename = os.path.join(self.PLAYBOOK_DIR, name + '.yaml')
        if os.path.exists(filename):
            choice = self._get_user_input(f"Are you sure you want to delete the playbook {name}? This cannot be undone. (yes/no): ")
            if choice.lower() == 'yes':
                try:
                    os.remove(filename)
                    # Remove from the internal cache if present
                    self.playbooks_data.pop(name, None)
                    self.log.info(f"Playbook {name} has been deleted.")
                except Exception as e:
                    self.log.error(f"Error deleting playbook {name}: {e}")
            else:
                self.log.info("Playbook deletion cancelled.")
        else:
            self.log.info(f"Playbook {name} does not exist.")

    def create_playbook(self, playbook_name):
        # Check if the playbook already exists
        playbook_path = os.path.join(self.PLAYBOOK_DIR, playbook_name + '.yaml')
        if os.path.exists(playbook_path):
            self.log.info(f"Playbook '{playbook_name}' already exists.")
            choice = input("Would you like to modify it instead? (yes/no): ")
            if choice.lower() == 'yes':
                self.modify_playbook(playbook_name)
            else:
                msg = "Creating a new playbook will overwrite the original one.\n"
                msg += "Are you sure you want to continue? (yes/no): "
                choice = self._get_user_input(msg)
                if choice.lower() != 'yes':
                    self._playbook_editor_menu(playbook_name)
                else:
                    self.log.info("Playbook creation canceled by the user.")
        else:
            self._playbook_editor_menu(playbook_name)

    def save_playbook(self, playbook_name):
        """Serialize and save the playbook's data to a YAML file"""
        playbook_data = self.playbooks_data.get(playbook_name)
        if playbook_data:
            # Convert the playbook data to a Playbook object
            playbook = Playbook(playbook_name, playbook_data)
            try:
                # Write the YAML data to a file
                with open(playbook.path, 'w') as file:
                    yaml.safe_dump(playbook._pack_data(), file, default_flow_style=False, sort_keys=False)
                self.log.info(f'Playbook "{playbook.name}" saved.')
            except Exception as e:
                self.log.error(f'Playbook "{playbook.name}" could not be saved: {e}.')
        else:
            self.log.error(f'Playbook "{playbook.name}" does not exist.')   

    @property
    def playbook_names(self):
        """list all playbooks names"""
        if not self._playbook_names:
            if not self.playbooks_data:
                self._load_all_playbooks_if_required()
            self._playbook_names = list(self.playbooks_data.keys())
        return self._playbook_names

class Playbook:
    PLAYBOOK_DIR = './playbooks'

    def __init__(self, playbook_name, playbook_data=None):
        self.name = playbook_name
        self.log = Log.get_instance()
        self.filename = f"{self.name}.yaml"
        self.path = os.path.join(self.PLAYBOOK_DIR, self.filename)
        self._integration_deps = []
        self._logic = []
        self._functions = []
        self._enabled = False
        self._data = playbook_data or {}
        self._exists = os.path.exists(self.path)
        self._is_running = False
        self.initialize() # Initialize the playbook
    
    def initialize(self):
        # This logic determines where to load the playbook data from disk, memory, or create a new playbook
        if self._exists and not self._data: # Load the playbook data from disk
            self.load()
        elif self._data: # Data was passed to the Playbook class from the PlaybookManager's cache
            self._unpack_data()
        else: # Create a new playbook (Initialized the playbook with default values)
            self.update() 
    
    def add_playbook_function(self, function):
        """Appends a new PlaybookFunction object the playbook."""
        try:        
            # Check if the function already exists in the playbook
            if function.name not in self.functions:
                self.functions.append(function.name)
            self.logic.append(function)
        except Exception as e:
            self.log.error(f"Error adding PlaybookFunction object '{function.name}' to {self.playbook.name} playbook logic: {e}")

        # Update the data in memory 

    def remove_playbook_function(self, function):
        """Remove the last PlaybookFunction object from a playbook's logic."""
        try:
            if function in self.logic:      
                self.logic.pop(function, None)
                self.log.info(f"PlaybookFunction object '{function.name}' removed from {self.playbook.name} playbook logic.")
                # If the none of the functions in the logic have the same name as the function being removed, 
                # then remove the function from the list of functions
                if not any(func.name == function.name for func in self.logic):
                    self.functions.remove(function.name)
                # Update the playbook's data in memory
                self._data['logic'] = [func.to_dict() for func in self.logic]

        except Exception as e:
            self.log.error(f"Error removing PlaybookFunction object '{function.name}' from {self.playbook.name} playbook logic: {e}")

    def select_playbook_function(self, index):
        """Select a playbook function from the playbook's logic."""
        try:
            return self.logic[index]
        except IndexError:
            self.log.error(f"Index {index} out of range for playbook {self.name}.")
            return None
        
    def replace_playbook_function(self, index, playbook_function):
        """Replace a playbook function at index n with the provided playbook"""
        try:
            self.logic[index] = playbook_function
        except IndexError:
            self.log.error(f"Index {index} out of range for playbook {self.name}.")
            return None
        except TypeError:
            self.log.error(f"Invalid type provided for playbook_function. Expected PlaybookFunction object.")
            return None

    def update(self):
        """Update a playbook's data in memory"""
        # Formats the data and then stores it in the self._data attribute
        try:
            data = self._pack_data()
            # Format the data correctly for internal cache
            data = data.get('Playbook', {})
            data.pop('name', None)
            self.data = data 
        except Exception as e:
            self.log.error(f"Error updating playbook {self.name}: {e}")

    def _pack_data(self):
        # Formats playbook data for saving
        try:
            data = {
                'Playbook': {
                    'name': self.name,
                    'enabled': self.enabled,  # Optionally, set this to False if you want it disabled by default
                    'integration_dependencies': self.integration_deps,
                    'logic': [func.to_dict() for func in self.logic]
                }
            }
            return data
        except Exception as e:
            self.log.error(f"Error packing playbook data: {e}")
            return {}

    def _unpack_data(self):
        # Unpack self._data to initialize playbook attributes
        self._integration_deps = self._data.get('integration_dependencies', [])
        self._logic = self._read_logic(self._data.get('logic', []))
        self._functions = self.get_unique_functions()
        self._enabled = self._data.get('enabled', False)

    def load(self):
        """Load a playbook's data from its YAML file."""
        try:
            with open(self.path, 'r') as file:
                data = yaml.safe_load(file) 
                playbook_data = data.get('Playbook', {}) # dict(): returns the Playbook dictionary from the yaml file using the 'Playbook' key
                if not playbook_data:
                    raise Exception(f"No valid playbook data found in {self.path}")
                self._name = playbook_data.get('name', self.name) # str(): Name of the playbook 
                self._enabled = playbook_data.get('enabled', False)  # bool(): Enabled status of the playbook
                self._integration_deps = playbook_data.get('integration_dependencies') # list(): list of integration dependencies
                self._logic = self._read_logic(playbook_data.get('logic')) # list(): returns list of PlaybookFunction objects with embedded logic
                self._functions = self.get_unique_functions() # list(): returns unique list of function names
                playbook_data.pop('name', None) # Remove the name key from the data
                self._data = playbook_data # store the extracted yaml data in the _data attribute  
        except Exception as e:
            print(f"Error loading playbook {self.name}: {e}")
            # Print the traceback
            print(f"An error occurred: {e}\n{traceback.format_exc()}")
    
    def get_unique_functions(self, dict_list=None):
        """Returns a unique list of functions from a list of dictionaries"""
        if dict_list:
            return list(set([func['function'] for func in dict_list if func['function'] not in self.functions]))
        else:
            return list(set(func.name for func in self.logic))

    def visualize(self):
        formatted_string = '\n'
        for i, function in enumerate(self.logic):
            level = 4
            formatted_string += level * '\t' + f"FUNCTION{i+1}: {function.name.upper()}\n"
            for key, value in function.trigger.items():
                formatted_string += (level + 1) * '\t' + f"{key.upper()}: {str(value).upper()}\n"
            # Display on_success for the current function
            on_success = function.on_success.upper() if function.on_success else "NONE"
            formatted_string += (level + 1) * '\t' + f"ON SUCCESS: {on_success}\n"
        return formatted_string
    
    def _read_logic(self, data):
        """Formats playbook logic for loading"""
        return [PlaybookFunction.from_dict(func) for func in data]

    # Getter and setter functions
    @property
    def exists(self):
        """Check if the playbook file exists."""
        return os.path.exists(self.path)   
    @property
    def data(self):
        return self._data
    @property
    def integration_deps(self):
        """Getter for integration_deps."""
        return self._integration_deps
    @property
    def logic(self):
        """Getter for logic."""
        return self._logic
    @property
    def functions(self):
        """Getter for functions."""
        if not self._functions:
            self._functions = self.get_unique_functions()
        return self._functions
    @property
    def enabled(self):
        """Getter for enabled."""
        return self._enabled
    @property
    def is_running(self):
        """Getter for is_running."""
        return self._is_running
    @data.setter
    def data(self, new_data):
        if isinstance(new_data, dict):
            self._data = new_data
        else:
            self.log.error(f"Invalid data type for playbook '{self.name}' data. Expected a dictionary.")
    @logic.setter
    def logic(self, logic):
        self._logic = logic
        self._data['logic'] = [func.to_dict() for func in logic]
    @integration_deps.setter
    def integration_deps(self, integration_deps):
        self._integration_deps = integration_deps
        self._data['integration_dependencies'] = integration_deps
    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        self._data['enabled'] = enabled
    @functions.setter
    def functions(self, functions):
        self._functions = functions
        self._data['functions'] = functions
    @is_running.setter
    def is_running(self, is_running):
        self._is_running = is_running
        
class PlaybookFunction:
    def __init__(self, name, trigger=None, on_success=None, on_fail=None, data_dependencies=None):
        self.name = name
        self.log = Log.get_instance()
        self.trigger = trigger if trigger is not None else {}
        self.trigger_type = self.trigger.get('type', '')
        self.trigger_duration = self.trigger.get('duration') if self.trigger_type == 'time' else None
        self.on_success = on_success
        self.on_fail = on_fail
        self.data_dependencies = data_dependencies

    def to_dict(self):
        # Return a dictionary representation of the playbook function
        # Nest the trigger correctly depending on the trigger_type
        trigger_data = {'type': self.trigger_type}
        if self.trigger_type == 'time':
            trigger_data['duration'] = self.trigger_duration
        data = {
            'function': self.name,
            'trigger': trigger_data,
        }
        if self.on_success is not None:
            data['on_success'] = self.on_success
        if self.on_fail is not None:
            data['on_fail'] = self.on_fail
        if self.data_dependencies is not None:
            data['data_dependencies'] = self.data_dependencies
        return data   
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name = data.get('function'),
            trigger = data.get('trigger', {}),
            on_success = data.get('on_success'),
            on_fail = data.get('on_fail'),
            data_dependencies = data.get('data_dependencies')
        )
        
    def execute(self, shared_data, config_mgr):
        """
        Execute the playbook function.
        `shared_data` is a NoneType object to share data between functions.
        """
        if self.trigger_type == 'time':
            # Convert duration to seconds if needed
            time.sleep(self.trigger_duration)

        elif self.trigger_type == 'always':
            # No specific action needed, will execute immediately
            pass

        # Check data dependencies
        needs = {dep: shared_data.get(dep) for dep in self.data_dependencies}
        if needs and any(value is None for value in needs.values()):
            raise Exception(f"Function {self.name} missing required data dependencies: {needs}")

        # Call the actual function
        function_instance = config_mgr.resolve_function(self.name)()
        try:
            result = function_instance.execute(shared_data)  # Assuming there's an execute method in the function class
            
            # Determine next function based on result
            next_function = self.on_success if result else self.on_fail

            # Logging the result
            self.log.info(f"Function {self.name} executed. Result: {result}")
            return next_function, result

        except Exception as e:
            self.log.error(f"Error in function {self.name}: {e}")
            return self.on_fail, {}
    
    def update_trigger(self, trigger):
        self.trigger = trigger

    def update_trigger_type(self, trigger_type):
        self.trigger_type = trigger_type
    
    def update_trigger_duration(self, duration):
        self.trigger_duration = duration
    
    def update_on_success(self, on_success):
        self.on_success = on_success

    def update_on_fail(self, on_fail):
        self.on_fail = on_fail
    
    def update_data_dependencies(self, data_dependencies):
        self.data_dependencies = data_dependencies

class PlaybookFlowchart:
    def __init__(self, playbook_logic):
        self.playbook_logic = playbook_logic
        self.node_map = {}
        self.start_node = pfc.Node('Start')
        self.log = Log.get_instance()

    def build_flowchart(self):
        self.node_map['Start'] = self.start_node
        last_node = self.start_node

        for step in self.playbook_logic:
            current_node = self._create_node(step)
            self.node_map[step['function']] = current_node
            last_node.connect(current_node)
            last_node = current_node

            if 'on_success' in step:
                on_success_node = self._get_or_create_node(step['on_success'])
                current_node.connect(on_success_node, yes='Success')

            if 'on_fail' in step:
                on_fail_node = self._get_or_create_node(step['on_fail'])
                current_node.connect(on_fail_node, no='Fail')

        self.fc = pfc.Flowchart(self.start_node)

    def _create_node(self, step):
        # Creates a new node if it doesn't exist or returns an existing one
        return self.node_map.get(step['function'], pfc.Node(step['function']))

    def _get_or_create_node(self, function_name):
        # Get the node if it exists, otherwise create a new one
        if function_name not in self.node_map:
            self.node_map[function_name] = pfc.Node(function_name)
        return self.node_map[function_name]

    def render_flowchart(self):
        if not hasattr(self, 'fc'):
            self.build_flowchart()
        return self.fc.flowchart()

class Log:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the logger with specific settings."""
        self.logger = logging.getLogger('PySOAR')
        self.set_level(logging.DEBUG)  # Default log level

        log_file = 'pysoar.log'
        file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
        console_handler = logging.StreamHandler()

        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_format = logging.Formatter('%(levelname)s: %(message)s')

        file_handler.setFormatter(file_format)
        console_handler.setFormatter(console_format)

        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def set_level(self, level):
        """Set the logging level."""
        self.logger.setLevel(level)

    # Convenience methods for logging
    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)

    def critical(self, message):
        self.logger.critical(message)

    def debug_requests_function(self, class_name, function_name, status, code, return_code, message, data):
        self.debug(f"{class_name}.{function_name} 'status': {status}")
        self.debug(f"{class_name}.{function_name} 'code': {code}")
        self.debug(f"{class_name}.{function_name} 'return_code': {return_code}")
        self.debug(f"{class_name}.{function_name} 'message': {message}")
        self.debug(f"{class_name}.{function_name} 'data': {data}")

