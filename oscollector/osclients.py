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

import logging
import sys
import time

import cinderclient.client
import glanceclient
import heatclient
import keystoneauth1.exceptions
import keystoneauth1.identity
import keystoneauth1.session
import keystoneclient.v3
import neutronclient.v2_0.client
import novaclient.client
import settings
import six  # noqa
import six.moves


logger = logging.getLogger(__name__)


class Common(object):
    """Common

    Retrieve keystone token
    """  # TODO(documentation)

    def __make_endpoint(self, endpoint):
        parse = six.moves.urllib.parse.urlparse(endpoint)
        return parse._replace(
            netloc='{}:{}'.format(
                self.controller_ip, parse.port)).geturl()

    def __init__(self, controller_ip, username, password,
                 project_name, user_domain_id, project_domain_id):
        self.controller_ip = controller_ip
        self.keystone_session = None

        if settings.DISABLE_SSL:
            auth_url = 'http://{0}:5000/v3'.format(self.controller_ip)
            path_to_cert = None
        else:
            auth_url = 'https://{0}:5000/v3'.format(self.controller_ip)
            path_to_cert = settings.PATH_TO_CERT

        insecure = not settings.VERIFY_SSL

        logger.debug('Auth URL is {0}'.format(auth_url))

        self.__keystone_auth = keystoneauth1.identity.v3.Password(
            auth_url=auth_url,
            username=username,
            password=password,
            project_name=project_name,
            user_domain_id=user_domain_id,
            project_domain_id=project_domain_id)

        self.__start_keystone_session(ca_cert=path_to_cert, insecure=insecure)

    @property
    def keystone(self):
        return keystoneclient.v3.Client(session=self.keystone_session)

    @property
    def glance(self):
        endpoint = self.__make_endpoint(
            self._get_url_for_svc(service_type='image'))
        return glanceclient.Client(
            version='1',
            session=self.keystone_session,
            endpoint_override=endpoint)

    @property
    def neutron(self):
        endpoint = self.__make_endpoint(
            self._get_url_for_svc(service_type='network'))
        return neutronclient.v2_0.client.Client(
            session=self.keystone_session,
            endpoint_override=endpoint)

    @property
    def nova(self):
        endpoint = self.__make_endpoint(
            self._get_url_for_svc(service_type='compute'))
        return novaclient.client.Client(
            version='2',
            session=self.keystone_session,
            endpoint_override=endpoint)

    @property
    def cinder(self):
        endpoint = self.__make_endpoint(
            self._get_url_for_svc(service_type='volume'))
        return cinderclient.client.Client(
            version='3',
            session=self.keystone_session,
            endpoint_override=endpoint)

    @property
    def heat(self):
        endpoint = self.__make_endpoint(
            self._get_url_for_svc(service_type='orchestration'))
        # TODO(parameter endpoint_override when heatclient will be fixed)
        return heatclient.v1.client(
            session=self.keystone_session,
            endpoint=endpoint)

    @property
    def keystone_access(self):
        return self.__keystone_auth.get_access(session=self.keystone_session)

    def _get_url_for_svc(
            self, service_type=None, interface='public',
            region_name=None, service_name=None,
            service_id=None, endpoint_id=None
    ):
        return self.keystone_access.service_catalog.url_for(
            service_type=service_type, interface=interface,
            region_name=region_name, service_name=service_name,
            service_id=service_id, endpoint_id=endpoint_id
        )

    def __start_keystone_session(
            self, retries=3, ca_cert=None, insecure=not settings.VERIFY_SSL):
        exc_type, exc_value, exc_traceback = None, None, None
        for i in six.moves.xrange(retries):
            try:
                if insecure:
                    self.keystone_session = (keystoneauth1.session.Session(
                                             auth=self.__keystone_auth,
                                             verify=False))
                elif ca_cert:
                    self.keystone_session = (keystoneauth1.session.Session(
                                             auth=self.__keystone_auth,
                                             verify=ca_cert))
                else:
                    self.keystone_session = (keystoneauth1.session.Session(
                                             auth=self.__keystone_auth))
                self.keystone_session.get_auth_headers()
                return

            except keystoneauth1.exceptions as exc:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err = "Try nr {0}. Could not get keystone token, error: {1}"
                logger.warning(err.format(i + 1, exc))
                time.sleep(5)
        if exc_type and exc_traceback and exc_value:
            logger.error(
                'Unable to establish connection with keystone. Exit...',
                exc_info=True)
            raise
        raise RuntimeError()
