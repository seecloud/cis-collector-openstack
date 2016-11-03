from collections import defaultdict
import requests
import json
import logging
import settings

logger = logging.getLogger(__name__)


class CISClient:
    """ CISClient - client for CIS backend

    CISClient purpose:
       - saving updated component state
       - getting previously saved component state
       - caching retrieved component state

    """
    def __init__(self, server_address, session=None):
        if not server_address:
            logger.error('No cis-server address specified. '
                         'Only in-memory storage will be used')
        self.server_address = server_address
        self.session = session
        self.cache = defaultdict(dict)

    def get_last_component_state(self, component):
        """Return previous component state

        Get previous component state from cache:
          - if there is no previous state in cache - get previous state from backend
          - if there is no previous state in backend - persist current state in backend,
            put current component state into cache as previous component state
          - return previous component state from cache

          :param component: component name (e.g. nova, keystone, neutron)
          :return: component state"""

        component_state = self.cache.get(component, None)
        if not component_state and component_state == settings.COMPONENT_EMPTY_STATE:
            # get data from test endpoint - replace in future with production api
            component_data = None
            headers = {'Content-Type': 'application/json', 'charset': 'utf-8'}
            api_endpoint = 'http://172.17.0.1:5000/api'
            logger.info("No data found in cache for {} component".format(component))
            try:
                req = requests.get('{0}/{1}'.format(api_endpoint, component), headers=headers)
                logger.debug("Get last state from db for {0} component".format(component))
                req_data = req.json()
                component_data = req_data.get('data', None)
                if not component_data:
                    self.cache[component] = settings.COMPONENT_EMPTY_STATE
            except requests.ConnectionError:
                logger.error("Unable to get last state from db for {0} component".format(component),
                             exc_info=True)

            if isinstance(component_data, unicode):
                component_data = json.loads(component_data)
            if component_data:
                self.cache[component] = component_data
        else:
            logger.debug("Return state from cache for {0} component".format(component))
        return self.cache.get(component, None)

    def save_component_state(self, component, service, service_data):
        """ Persist current component state into backend
        :param component: component name (e.g. nova, keystone, neutron)
        :param service: component's service name (e.g. for keystone: users)
        :param service_data: service state, which should be persisted
        :return: boolean as result of operation
        """
        # Todo: replace with method for CIS API when last will be available

        headers = {'Content-Type': 'application/json', 'charset': 'utf-8'}
        api_endpoint = "http://{0}:5000/api".format(settings.CIS_SERVER)

        try:
            requests.post('{0}/{1}/{2}'.format(api_endpoint, component, service),
                          headers=headers, data=json.dumps(service_data))
            logger.debug("Update {0}:{1} state on backend".format(component, service))
        except requests.ConnectionError:
            logger.error("Unable to update {0}:{1} state on backend".format(component, service),
                         exc_info=True)

        if not self.cache.get(component, None):
            self.cache[component] = {}
        self.cache[component][service] = service_data
        logger.debug("Update {0}:{1} state in cache".format(component, service))

    @staticmethod
    def register_schema(schema, component, service):
        resource_schema = dict(schema=schema, component=component, service=service)
        pass
