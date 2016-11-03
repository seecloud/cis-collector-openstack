import logging
import json
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


def var_as_bool(var=None, default=False):
    return var if isinstance(var, bool) else _boolean_states.get(var, default)


ELASTICSEARCH_TYPE_MAPPING = {
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

    supported_schemas = {}

    def __init__(self):
        logger.warning("Use 'ResourceFactory.setup() for initialization")

    @classmethod
    def setup(cls, components):

        logger.info('Looking for available resource schemas')

        for component in components:

            try:
                with open('schema/{0}.json'.format(component)) as cfg:
                    cls.supported_schemas[component] = json.load(cfg)
                logger.info('Found schemas for {0} component'
                            .format(component))
                logger.info('List of available resource schemas: {0}'
                            .format(", ".join(cls.supported_schemas[component].keys())))

            except (IOError, ValueError):
                logger.error('Error while reading resource schemas for {0} component'
                             .format(component),
                             exc_info=True)

    @classmethod
    def create_resource(cls, resource_raw, component, service):

        if not isinstance(resource_raw, dict):
            resource = resource_raw.__dict__.get('_info')
        else:
            resource = resource_raw

        if cls.supported_schemas[component][service].get('root', None):
            resource = resource.get(cls.supported_schemas[component][service]['root'])
        root_id = cls.supported_schemas[component][service]['root_id']
        resource_id = resource.pop(root_id)
        resource_body = ResourceFactory._serialize_resource(resource,
                                                            cls.supported_schemas[component][service])

        try:
            validate(resource_body, cls.supported_schemas[component][service])
            return {str(resource_id): resource_body}
        except ValidationError:
            logger.error("{0}::{1} resource with id {2} has wrong schema"
                         .format(component, service, resource_id),
                         exc_info=True)

    @staticmethod
    def _serialize_resource(resource_raw, schema):
        resource = {}
        if schema.get('properties', None):
            for field, value in schema.get('properties', {}).iteritems():
                if value['type'] == 'object':
                    resource[field] = ResourceFactory._serialize_resource(resource_raw[field],
                                                                          value)
                elif value['type'] == 'array':
                    resource[field] = []
                    for item in resource_raw[field]:
                        temp = ResourceFactory._serialize_resource(item, value.get('items', {}))
                        if temp:
                            resource[field].append(temp)
                else:
                    resource[field] = ResourceFactory._cust_object(resource_raw, field, value['type'])
        else:
            resource = resource_raw
        return resource

    @staticmethod
    def _cust_object(resource, field, schema_type):
        if resource.get(field, None) is not None:
            proper_field = ELASTICSEARCH_TYPE_MAPPING[schema_type](resource[field])
        else:
            proper_field = ELASTICSEARCH_TYPE_MAPPING[schema_type]()
        return proper_field
