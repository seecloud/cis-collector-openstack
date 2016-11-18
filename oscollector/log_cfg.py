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
import logging.config

import settings


def setup_logger():
    """Setup logging configuration

    Logger configured on import
    """

    try:
        logging.config.dictConfig(settings.DEV_LOGGING_CONFIG)
        configured_logging = True
        logging.info('Logging configured with application configuration')
    except SyntaxError:
        configured_logging = False
        logging.info('Logging setup from application configuration failed. '
                     'Default configuration will be applied')

    if not configured_logging:
        logging.basicConfig(level=logging.INFO)

setup_logger()
