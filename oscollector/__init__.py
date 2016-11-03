from osclients import Common
import envutils
import pprint
from collections import defaultdict

creds = envutils.fake_get_creds_from_env_vars()
client = Common(**creds)
pp = pprint.PrettyPrinter(indent=4)

nc = client.glance

from resource_factory import ResourceFactory
ResourceFactory.setup(['keystone', 'nova', 'neutron', 'cinder', 'glance'])


for item in nc.images.list():
    pp.pprint(item.__dict__['_info'])
    o = ResourceFactory.create_resource(item, 'glance', 'images')
    pp.pprint(o)
