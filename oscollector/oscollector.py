import envutils
import settings
from osclients import Common
from service_collector import ServiceCollector
from resource_factory import ResourceFactory
from deepdiff import DeepDiff
from keystoneauth1 import exceptions
from cisclient import CISClient
from collections import defaultdict
import logging
import json
import exception
import threading
import time

logger = logging.getLogger(__name__)


class OSCollector:
    """ OpenStack state collector

    OSCollector collects information about OpenStack components and services state.
    Components for monitoring are listed in config.json configuration. If there is no
    valid config.json - default settings from settings.py configuration will be used.

    OSCollector operates with two entities:
      - component - OpenStack component. Example: Nova, Keystone, Neutron
      - service - component service. Example for keystone component: users, roles, projects

    For collecting data OSCollector uses ServiceCollector.
    For communication with backend OSCollector uses CISClient

    Workflow:
      1. Get current component state
      2. Get previous component state from cache
       \
        - if there is no previous state in cache - get previous state from backend
         \
          - if there is no previous state in backend - persist current state in backend,
            put current component state into cache as previous component state
        - return previous component state from cache
      3. Compare component services key by key and return changes (created, deleted, updated)
      4. Persist changed services into backend
      5. Update cache
    """

    cache = {}

    def __init__(self):

        self.osclient = None
        self.cisclient = None
        self.init_session()

        try:
            with open(settings.DEFAULT_CONFIG_FILE) as cfg:
                self.config = json.load(cfg)
            logger.info('Read collector configuration from {} '
                        .format(settings.DEFAULT_CONFIG_FILE))
        except (IOError, ValueError):
            self.config = settings.DEFAULT_CONFIG
            logger.warning('Can not open DEFAULT_CONFIG_FILE. DEFAULT_CONFIG will be used',
                           exc_info=True)

        if not self.config.get('components', None):
            logger.error('List with components for collecting data is empty')
            raise exception.CollectorError(
                'List with components for collecting data is empty')

        ResourceFactory.setup(self.config['components'])

        self.validate_configuration()

    def init_session(self):
        credentials = envutils.get_creds_from_env_vars()
        self.osclient = Common(**credentials)
        self.cisclient = CISClient(settings.CIS_SERVER)

    def validate_configuration(self):
        os_services = [component.name for component in self.osclient.keystone.services.list()]
        invalid_components = []

        for component in self.config['components'].keys():
            if component not in os_services:
                invalid_components.append(component)
                logger.warning(" ".join(["Component {0}".format(component),
                                         "from configuration is not available in OpenStack services.",
                                         "It will be removed from collector"]))
            if component not in ResourceFactory.supported_schemas \
                    and component not in invalid_components:
                invalid_components.append(component)
                logger.warning(" ".join(["Component {0}".format(component),
                                         "from configuration has no proper resource schemas description.",
                                         "It will be removed from collector"]))

            if component not in invalid_components:
                invalid_services = defaultdict(list)
                for service in self.config['components'][component]:
                    if service not in ResourceFactory.supported_schemas[component].keys():
                        invalid_services[component].append(service)
                        logger.warning(" ".join(["Service {0}::{1}".format(component, service),
                                                 "from configuration has no proper resource schema description.",
                                                 "It will be removed from collector"]))
                invalid_components.append(dict(invalid_services))

        for invalid_component in invalid_components:
            if isinstance(invalid_component, dict):
                for component, services in invalid_component.iteritems():
                    for service in services:
                        self.config['components'][component].remove(service)
            else:
                del self.config['components'][invalid_component]

    def collect(self):
        """ Thread runner

        This function spawns threads for syncing current and previous states
        and sleep main thread for configured delay(seconds) in configuration
        """
        threads = []
        for component, services in self.config['components'].iteritems():
            p = threading.Thread(target=self.syncup, args=(component, services))
            threads.append(p)
            p.start()

        start = time.time()
        time.sleep(self.config['delay'])
        while time.time() - start <= self.config['delay'] * 2:
            if any(p.is_alive() for p in threads):
                time.sleep(.1)
            else:
                break
        else:
            logger.warning("Timed out, something goes wrong in collector process")

    def syncup(self, component, services):
        """ Synchronize component services
        :param component: component name (e.g. nova, keystone, neutron)
        :param services: list of component services (e.g. for keystone: users, projects, roles)
        """
        current_state = None
        try:
            current_state = ServiceCollector.collect(self.osclient, component, services)
        except exceptions.ClientException:
            logger.error('Keystone error occurs. Try to reinit session',
                         exc_info=True)
            self.init_session()
        last_state = self.cisclient.get_last_component_state(component)
        if not last_state and current_state:
            for service in current_state.keys():
                logger.info("No last state found for service {0} in component {1}."
                            .format(service, component))
                self.cisclient.save_component_state(component, service, current_state[service])
            last_state = current_state

        changes = {}
        for service in current_state.keys():
            if current_state[service] == settings.SERVICE_INVALID_STATE:
                self.config['components'][component].remove(service)
                logger.warning('Service {0} was removed from configuration due to invalid state'
                               .format(service))
            else:
                changes[service] = self.compare(current_state.get(service, {}), last_state.get(service, {}),
                                                component, service)

        for service in changes.keys():
            if changes[service]:
                self.cisclient.save_component_state(component, service, current_state[service])
        return

    def compare(self, current, last, component, service):
        """ Compare current and previous service states

        Compare is performed key by key.
        Key order ignored.
        List of keys, specified in configuration in 'ignore_keys' - ignored.
        List of collected changes available in debug information.
        :param current: current service state
        :param last: previous service state
        :param component: component name (e.g. nova, keystone, neutron)
        :param service: component's service name (e.g. for keystone: users)
        :return: dict with changes by service. Only objects ids returned. E.g.:
                 changes: {
                   'keystone': {
                     'created': [user_object_ids]
                     'updated': [[project_object_ids]]
                   },
                   'neutron': {
                     'deleted': [router_object_ids]
                     'updated': [[port_object_ids]]
                   }
                }

        """
        changes = {}

        for key in set(current.viewkeys()).symmetric_difference(set(last.viewkeys())):
            if key not in last:
                logger.info('Object with id {0} was created in {1}:{2}'
                            .format(key, component, service))
                changes.setdefault('created', []).append(
                    {
                        key: current[key]
                    }
                )
            else:
                logger.info('Object with id {0} was deleted in {1}:{2}'
                            .format(key, component, service))
                changes.setdefault('deleted', []).append(
                    {
                        key: last[key]
                    }
                )

        for key in current.viewkeys() & last.viewkeys():
            diff = DeepDiff(current[key], last[key],
                            ignore_order=True,
                            exclude_paths={"root['{0}']".format(key) for key in self.config.get('ignore_keys', {})})
            if diff:
                logger.info('Object with id {0} was changed in {1}:{2}'
                            .format(key, component, service))
                logger.debug('Changes: {0}'.format(str(diff)))
                changes.setdefault('updated', []).append(
                    {
                        key: current[key]
                    }
                )

        return changes
