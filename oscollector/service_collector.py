#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import logging

import resource_factory
import settings

logger = logging.getLogger(__name__)


class ServiceCollector:
    """Collector for OpenStack component services states

    """
    def __init__(self):
        logger.warning(
            "Use 'collect(service, client) method for collecting data")

    @classmethod
    def __collect_keystone(cls, client, services):
        """Keystone collector. Not used directly. Called from collect function.

        :param client: OpenStack client with proper session
        :param services: list of services for collecting data from
        :return keystone_state: dict with collected data by services as keys
        """

        kc = client.keystone
        keystone_state = collections.defaultdict(dict)

        for service in services:
            try:
                service_client = kc.__dict__[service]
                for item in service_client.list():
                    keystone_state[service].update(
                        resource_factory.ResourceFactory
                        .create_resource(item, 'keystone', service))

            except KeyError:
                logger.warning(" ".join(["There is no {0} service in keystone."
                                        .format(service),
                                         "It will be removed",
                                         "from collector configuration"]),
                               exc_info=True)
                keystone_state[service] = settings.SERVICE_INVALID_STATE

        return keystone_state

    @classmethod
    def collect(cls, client, component, services):
        """Wrapper around other OpenStack component collectors

        :param client: OpenStack client with proper session
        :param component: OpenStack component name. E.g. 'nova', 'keystone'
        :param services: list of component services for collecting data from
        :return data: dict with collected component data by services as keys
        """
        try:
            component_collector = cls.get_collector(component)
            data = component_collector(client, services)

        except BaseException:
            # Todo: submit information about invalid component state
            logger.error('Can not collect {0} component data'
                         .format(component),
                         exc_info=True)
            raise

        return data

    @classmethod
    def get_collector(cls, component):
        colectors = {
            'keystone': cls.__collect_keystone
        }
        return colectors.get(component, lambda *args: None)
