import os

_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False,
                   'False': False, 'True': True}


def get_env_var_as_bool(name, default):
    value = os.environ.get(name, '')
    return _boolean_states.get(value.lower(), default)

CIS_SERVER = os.environ.get('CIS_SERVER', None)
DNS = os.environ.get('DNS', '8.8.8.8')
PUBLIC_TEST_IP = os.environ.get('PUBLIC_TEST_IP', '8.8.8.8')

DISABLE_SSL = get_env_var_as_bool('DISABLE_SSL', True)
VERIFY_SSL = get_env_var_as_bool('VERIFY_SSL', False)
SSL_CN = os.environ.get('SSL_CN', 'msaos')
SSL_CERTS_DIR = os.environ.get('SSL_CERTS_DIR', os.getcwd())
if not os.path.exists(SSL_CERTS_DIR):
    os.makedirs(SSL_CERTS_DIR)
USER_OWNED_CERT = get_env_var_as_bool('USER_OWNED_CERT', True)
PATH_TO_CERT = os.environ.get('PATH_TO_CERT', os.path.join(
    SSL_CERTS_DIR, 'ca.crt'))
PATH_TO_PEM = os.environ.get('PATH_TO_PEM', os.path.join(
    SSL_CERTS_DIR, 'ca.pem'))

COMPONENT_EMPTY_STATE = 'empty'
SERVICE_INVALID_STATE = 'invalid'
SERVICE_VALID_STATE = 'valid'
DEFAULT_CONFIG_FILE = 'config.json'


DEFAULT_CONFIG = {
    "delay": 5,
    "components": {

        "keystone": [
            "projects",
            "domains",
            "users",
            "roles",
            "services"
        ],
        "nova": [
            "servers",
            "flavors",
            "keypairs",
            "hypervisors",
            "quotas"
        ],
        "neutron": [
            "networks",
            "routers",
            "subnets",
            "ports",
            "security_groups",
            "security_group_rules",
            "floatingips",
            "quotas",
            "flavors"
        ],
        "glance": [
            "images"
        ],
        "cinder": [
            "volumes",
            "backups",
            "volume_snapshots"
        ],
        "heat": [
            "stacks"
        ]
    },
    "ignore_keys": [
      "vcpus",
      "free_ram_mb",
      "hypervisor_version",
      "memory_mb",
      "disk_available_least",
      "free_disk_gb",
      "hypervisor_type",
      "cpu_info",
      "local_gb",
      "local_gb_used"
    ]
}

LOG_PATH = os.environ.get('LOGS_DIR', '/'.join([os.getcwd(), 'logs']))
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)
DEV_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'basic',
            'stream': 'ext://sys.stdout'
        },

        'info_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'basic',
            'filename': os.path.join(LOG_PATH, 'info.log'),
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        },

        'error_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'basic',
            'filename': os.path.join(LOG_PATH, 'errors.log'),
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        }
    },

    'loggers': {
        'oscollector': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'service_collector': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'resource_factory': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'cisclient': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    },

    'root': {
        'level': 'INFO',
        'handlers': ['info_file_handler', 'error_file_handler'],
    }
}

# no console ouptput
PROD_LOGGING = DEV_LOGGING_CONFIG.copy()
PROD_LOGGING.update({
    'root': {
        'level': 'INFO',
        'handlers': ['info_file_handler', 'error_file_handler']
    }
})
