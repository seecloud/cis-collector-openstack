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

import json
import logging

import jsonschema

logger = logging.getLogger(__name__)


def var_as_bool(var=None, default=False):
    """Casting bool representation to proper boolean value

    :param var: input parameter for casting
    :param default: default value for empty cast parameter
    :return: proper boolean representation of the input parameter
    """
    return var if isinstance(var, bool) else _boolean_states.get(var, default)


TYPE_MAPPING = {
    "integer": lambda *x: -1 if len(x) == 0 else int(x[0]),
    "string": str,
    "object": dict,
    "array": list,
    'boolean': var_as_bool
}

_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False,
                   'False': False, 'True': True}


class ResourceFactory:
    """ResourceFactory generator

    ResourceFactory purpose is creating OpenStack resources objects
    with proper schema
    """
    supported_schemas = {}

    def __init__(self):
        logger.warning("Use 'ResourceFactory.setup() for initialization")

    @classmethod
    def setup(cls, components):
        """Initial configuration of the ResourceFactory

        Method looks for schemas for OpenStack components
        :param components: list with openstack components,
        taken from collector configuration
        """
        logger.info('Looking for available resource schemas')

        for component in components:

            try:
                with open('schema/{0}.json'.format(component)) as cfg:
                    cls.supported_schemas[component] = json.load(cfg)
                logger.info('Found schemas for {0} component'
                            .format(component))
                logger.info('List of available resource schemas: {0}'
                            .format(", ".join(
                                    cls.supported_schemas[component].keys())))

            except (IOError, ValueError):
                logger.error(
                    'Error while reading resource schemas for {0} component'
                    .format(component),
                    exc_info=True)

    @classmethod
    def create_resource(cls, resource_raw, component, service):
        """Preparing item and schema of component::service type

        :param resource_raw: item of type component::service
        :param component: OpenStack component (e.g. 'nova', 'keystone')
        :param service:  component's service (e.g. 'projects' for keystone)
        :return: resource with identifier as key and value,
        generated by component::service schema
        """
        if not isinstance(resource_raw, dict):
            resource = resource_raw.__dict__.get('_info')
        else:
            resource = resource_raw

        if cls.supported_schemas[component][service].get('root', None):
            resource = (resource
                        .get(cls
                             .supported_schemas[component][service]['root']))
        root_id = cls.supported_schemas[component][service]['root_id']
        resource_id = resource.pop(root_id)
        service_schema = cls.supported_schemas[component][service]
        resource_body = (ResourceFactory.
                         _serialize_resource(resource, service_schema))

        try:
            jsonschema.validate(resource_body,
                                cls.supported_schemas[component][service])
            return {str(resource_id): resource_body}
        except jsonschema.ValidationError:
            logger.error("{0}::{1} resource with id {2} has wrong schema"
                         .format(component, service, resource_id),
                         exc_info=True)

    @staticmethod
    def _serialize_resource(resource_raw, schema):
        """Actual generating of the new resource by provided schema

        :param resource_raw: resource with data
        :param schema: jsonschema draft-4 schema
        :return: resource without identifier
        """
        resource = {}
        if schema.get('properties', None):
            for field, value in schema.get('properties', {}).iteritems():
                if value['type'] == 'object':
                    resource[field] = (ResourceFactory.
                                       _serialize_resource(resource_raw[field],
                                                           value))
                elif value['type'] == 'array':
                    resource[field] = []
                    for item in resource_raw[field]:
                        temp = (ResourceFactory.
                                _serialize_resource(item,
                                                    value.get('items', {})))
                        if temp:
                            resource[field].append(temp)
                else:
                    resource[field] = (ResourceFactory.
                                       _cust_object(resource_raw,
                                                    field, value['type']))
        else:
            resource = resource_raw
        return resource

    @staticmethod
    def _cust_object(resource, field, schema_type):
        """Casting resource field with schema_type

        :param resource: resource with data
        :param field: resource key
        :param schema_type: type for casting resource[field] to
        :return: casted with proper type resource[field]
        """
        if resource.get(field, None) is not None:
            proper_field = TYPE_MAPPING[schema_type](resource[field])
        else:
            proper_field = TYPE_MAPPING[schema_type]()
        return proper_field
