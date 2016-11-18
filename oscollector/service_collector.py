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
    def __collect_nova(cls, client, services):
        """Nova collector. Not used directly. Called from collect function.

        :param client: OpenStack client with proper session
        :param services: list of services for collecting data from
        :return nova_state: dict with collected data by services as keys
        """

        nc = client.nova
        nova_state = collections.defaultdict(dict)

        for service in services:
            if service in ['flavors', 'hypervisors', 'images', 'keypairs']:
                for item in nc.__dict__[service].list():
                    nova_state[service].update(
                        resource_factory.ResourceFactory
                        .create_resource(item, 'nova', service))

            elif service == 'servers':
                for item in nc.servers.list(search_opts={'all_tenants': 1}):
                    nova_state[service].update(
                        resource_factory.ResourceFactory
                        .create_resource(item, 'nova', service))

            elif service == 'quotas':
                item = nc.quotas.get(None)
                nova_state[service].update(
                    resource_factory.ResourceFactory
                    .create_resource(item, 'nova', service))

            else:
                logger.warning(" ".join(["There is no {0} service in nova"
                                        .format(service),
                                         "It will be removed",
                                         "from collector configuration"]),
                               exc_info=True)

        return nova_state

    @classmethod
    def __collect_neutron(cls, client, services):
        """Neutron collector. Not used directly. Called from collect function.

        :param client: OpenStack client with proper session
        :param services: list of services for collecting data from
        :return neutron_state: dict with collected data by services as keys
        """

        nc = client.neutron
        neutron_state = collections.defaultdict(dict)

        neutron_services = {
            'networks': nc.list_networks,
            'routers': nc.list_routers,
            'subnets': nc.list_subnets,
            'ports': nc.list_ports,
            'security_groups': nc.list_security_groups,
            'security_group_rules': nc.list_security_group_rules,
            'floatingips': nc.list_floatingips,
            'quotas': nc.list_quotas,  # Todo: add schema
            'flavors': nc.list_flavors  # Todo: add schema
        }

        for service in services:

            service_data = neutron_services.get(service,
                                                lambda *args: None)()

            if not service_data:
                logger.warning(" ".join(["There is no {0} service in neutron."
                                        .format(service),
                                         "It will be removed",
                                         "from collector configuration"]),
                               exc_info=True)
                neutron_state[service] = settings.SERVICE_INVALID_STATE
            else:

                for neutron_resource, values in service_data.items():
                    for item in values:
                        neutron_state[neutron_resource].update(
                            resource_factory.ResourceFactory
                            .create_resource(item, 'neutron',
                                             neutron_resource))

        return neutron_state

    @classmethod
    def __collect_glance(cls, client, services):
        """Glance collector. Not used directly. Called from collect function.

        :param client: OpenStack client with proper session
        :param services: list of services for collecting data from
        :return glance_state: dict with collected data by services as keys
        """

        gc = client.glance
        glance_state = collections.defaultdict(dict)

        for service in services:
            try:
                service_client = gc.__dict__[service]
                for item in service_client.list():
                    glance_state[service].update(
                        resource_factory.ResourceFactory
                        .create_resource(item, 'glance', service))
            except KeyError:
                logger.warning(" ".join(["There is no {0} service in glance."
                                        .format(service),
                                         "It will be removed",
                                         "from collector configuration"]),
                               exc_info=True)
                glance_state[service] = settings.SERVICE_INVALID_STATE

        return glance_state

    @classmethod
    def __collect_cinder(cls, client, services):
        """Cinder collector. Not used directly. Called from collect function.

        :param client: OpenStack client with proper session
        :param services: list of services for collecting data from
        :return cinder_state: dict with collected data by services as keys
        """

        cc = client.cinder
        cinder_state = collections.defaultdict(dict)

        # Todo: find cinder backups structure ?

        for service in services:
            try:
                service_client = cc.__dict__[service]
                for item in (service_client
                             .list(search_opts={'all_tenants': 1})):
                    cinder_state[service].update(
                        resource_factory.ResourceFactory
                        .create_resource(item, 'cinder', service))
            except KeyError:
                logger.warning(" ".join(["There is no {0} service in cinder."
                                        .format(service),
                                         "It will be removed",
                                         "from collector configuration"]),
                               exc_info=True)
                cinder_state[service] = settings.SERVICE_INVALID_STATE
        return cinder_state

    @classmethod
    def __collect_heat(cls, client, services):
        """Heat collector. Not used directly. Called from collect function.

        :param client: OpenStack client with proper session
        :param services: list of services for collecting data from
        :return heat_state: dict with collected data by services as keys
        """

        hc = client.heat
        heat_state = collections.defaultdict(dict)

        for service in services:
            try:
                service_client = hc.__dict__[service]
                for item in service_client.list():
                    data = item.__dict__.get('_info')
                    heat_state[service][str(data.pop('id'))] = data
            except KeyError:
                logger.warning(" ".join(["There is no {0} service in heat."
                                        .format(service),
                                         "It will be removed",
                                         "from collector configuration"]),
                               exc_info=True)
                heat_state[service] = settings.SERVICE_INVALID_STATE

        return heat_state

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
            'keystone': cls.__collect_keystone,
            'nova': cls.__collect_nova,
            'neutron': cls.__collect_neutron,
            'glance': cls.__collect_glance,
            'cinder': cls.__collect_cinder,
            'heat': cls.__collect_heat
        }
        return colectors.get(component, lambda *args: None)
