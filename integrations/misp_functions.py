"""Integration Specific Functions"""
from pymisp import ExpandedPyMISP as PyMISP
from pymisp import MISPEvent
from pymisp import MISPAttribute
from pymisp import MISPTag
from classes import Log

class MispFunction:
    """Class for MISP functions."""
    # Certificate paths
    CERT_PATH = './certs/api_user.crt'
    CA_CERT_PATH = './certs/CA.crt'
    KEY_PATH = './certs/api_user.key'
    # This dictionary lists potential feeds for each data type
    # Note that the feed ID changes every time the feed is toggled
    # The key is the data type and the value is the 
    # name = misp.feeds()[index]['Feed'].get('name')
    FEEDS_BY_DATA_TYPE = {
        'ip-dst': ['firehol_level1', 'malsilo.ipv4'],
        'domain': ['Domains from High-Confidence DGA-based C&C Domains Actively Resolving', 'malsilo.domain'],
        'url': ['CyberCure - Blocked URL Feed', ],
        'hostname': ['hostname_feed_1'],
        'hash': ['CyberCure - Hash Feed', 'http://cybercrime-tracker.net hashlist'],
        'filename': ['filename_feed_id_1', 'filename_feed_id_2'],
        'email': ['email_feed_id_1', 'email_feed_id_2']
    }
    def __init__(self, misp_init):
        """Initialize the MISP class."""
        self.log = Log.get_instance()
        try:
            self.misp_api = PyMISP(misp_init.url, 
                misp_init.api_key, 
                misp_init.ssl,
                misp_init.verifycert
                )
        except Exception as e:
            self.log.error(f"Error initializing MISP: {e}")
            return None
        self.enabled_feeds = self.get_enabled_feeds()
        self._feeds = self._get_feeds()

    def get_enabled_feeds(self):
        """Get the list of enabled feeds from MISP."""
        self.log.info("Getting enabled feeds from MISP...")
        enabled_feeds = {}
        for feed in self.feeds:
            if feed['Feed']['enabled']:
                feed_type = next((data_type for data_type, feed_list in self.FEEDS_BY_DATA_TYPE.items() if feed['Feed']['name'] in feed_list), None)
                enabled_feeds[feed['Feed']['name']] = {
                    'feed_id': feed['Feed']['id'],
                    'data_types': feed_type,
                    'metadata': feed['Feed']
                }
        # Remove the name and id from the metadata
        for feed_name, feed_data in enabled_feeds.items():
            feed_data['metadata'].pop('name', None)
            feed_data['metadata'].pop('id', None)
        self.log.debug(f"Enabled feeds: {enabled_feeds}")
        return enabled_feeds

    def send_to_misp(self, event):
        """Send an event to MISP."""
        pass

    def get_misp_event(self, event_id):
        """Get an event from MISP."""
        return self.misp_api.get_event(event_id, pythonify=True)

    def create_misp_event(self, info, distribution, threat_level_id, analysis, date=None):
        """Create a new event in MISP."""
        '''
        add_event(event: pymisp.mispevent.MISPEvent, pythonify: bool = False, metadata: bool = False) -> Union[Dict, pymisp.mispevent.MISPEvent] method of pymisp.api.PyMISP instance
        Add a new event on a MISP instance: https://www.misp-project.org/openapi/#tag/Events/operation/addEvent
        :param event: event to add
        :param pythonify: Returns a PyMISP Object instead of the plain json output
        :param metadata: Return just event metadata after successful creating
        '''
        event = MISPEvent()
        event.info = info
        event.distribution = distribution
        event.threat_level_id = threat_level_id
        event.analysis = analysis
        if date:
            event.date = date

        # Add the event to MISP using ExpandedPyMISP
        try:
            response = self.misp_api.add_event(event, pythonify=True)
            return response
        except Exception as e:
            # Handle exceptions such as invalid event format or API errors
            raise e

    def enable_threat_feed(self, feed_id):
        """Enable a threat feed in MISP by its id or name"""
        try:
            self.misp_api.enable_feed(feed_id)
        except Exception as e:
            raise e

    def disable_threat_feed(self, feed_id):
        """Disables a threat feed in MISP by its id or name."""
        try:
            self.misp_api.disable_feed(feed_id)
        except Exception as e:
            raise e
    
    def check_enabled_by_name(self, feed_name):
        """Check if a feed is enabled in MISP by its feed_id."""
        if next((feed['Feed'] for feed in self.feeds if feed['Feed']['name'] == feed_name and feed['Feed']['enabled']), None):
            return True
        else:
            return False

    def ensure_feed_enabled(self, data_type):
        # Get list of potential feeds for this data type
        potential_feeds = (self.FEEDS_BY_DATA_TYPE.get(data_type, []))

        # Find an enabled feed from the potential feeds
        enabled_feed_name = next((feed for feed in potential_feeds if feed in self.enabled_feeds), None)

        if enabled_feed_name:
            # A feed for this data type is already enabled
            return

        # If we reached here, we need to enable a feed for this data type
        feed_to_enable = potential_feeds[0]  # You can modify the logic to choose which feed to enable if there are multiple
        if feed_to_enable:
            # Retrieve the corresponding MISP's feed ID 
            feed_data = self._get_misp_feed_by_name(feed_to_enable)

            # Toggle the feed using the MISP's feed ID and cache it
            try:
                self.enable_threat_feed(feed_data.get('id'))
                self._cache_feed(feed_data.get('id'))

                # Verify the feed is now enabled
                if self.check_enabled_by_name(feed_to_enable):
                    print(f"Successfully enabled feed {feed_to_enable}")

            except Exception as e:
                return (f"Error enabling feed {feed_to_enable}: {e}")
            
            feed_data.pop('enabled', None)  # Remove the enabled status from the feed data (not needed anymore
            feed_data.pop('name', None)
            feed_id = feed_data.pop('ip', None)
            # Update the status of this feed in your enabled_feeds dictionary
            self.enabled_feeds[feed_to_enable] = {
                'feed_id': feed_id,  # Fetching the feed ID again for assurance
                'data_types': data_type,
                'metadata': feed_data
            }
            return True
        
    def _cache_feed(self, feed_id):
        """Cache the given feed."""
        try:
            self.misp_api.cache_feed(feed_id)
        except Exception as e:
            raise e

    def _get_cached_feed(self, feed_id):
        """Get the cached feed data."""
        try:
            return self.misp_api.get_feed(feed_id)
        except Exception as e:
            raise e

    def get_event_id(self, feed_id):
        """Get the event ID from the cached feed."""
        return self._get_cached_feed(feed_id)['Feed']['event_id']

    def get_event_data_by_type(self, data_type, feed_id='14'):
        """Get blacklisted IP addresses from a cached feed."""
        # Get event ID from the cached feed and fetch the event data
        #event_id = self.get_event_id(feed_id)
        event_id = self.get_event_id(feed_id)
        event_data = self.get_misp_event(event_id)

        # Extract attributes from the event data
        attributes = event_data.get('Attribute', [])
        
        # Filter attributes by the data type (returns a list of MISPAttribute Objects)
        metadata = [attr for attr in attributes if attr['type'] == data_type]  # List comprehension to filter out 'ip-dst' types
        
        # Initialize a list to hold all the target values
        values = []
        values.append([attr['value'] for attr in metadata])

        # Only the return the first five values as a list (Testing only)
        return values[0][25:30]
    
    def _search_attributes(self, attribute_type, value=None):
        """Search for attributes in MISP."""
        search_params = {
            'type_attribute': attribute_type,
            'value': value,  # You can leave out value to get all attributes of a certain type
            'to_ids': True,  # Assuming you only want attributes marked for IDS (Intrusion Detection System)
            'include_context': True,
        }
        try:
            response = self.misp_api.search('attributes', **search_params)
            return response
        except Exception as e:
            raise e

    def _get_misp_feed_by_name(self, feed_name):
        """Get a feed from MISP."""
        feed_data = next((feed['Feed'] for feed in self.feeds if feed['Feed']['name'] == feed_name), {})
        return feed_data
    
    def _get_misp_feed_by_id(self, feed_id):
        """Get a feed from MISP."""
        feed_data = next((feed['Feed'] for feed in self.feeds if feed['Feed']['id'] == feed_id), {})
        return feed_data

    def _get_feeds(self):
        """Get the list of feeds from MISP."""
        try:
            # Load the default list of feeds
            self.misp_api.load_default_feeds()
            all_feeds = self.misp_api.feeds()
            return all_feeds
        except:
            return []
    
    @property
    def feeds(self):
        """Get the list of feeds from MISP."""
        return self._get_feeds()
        
