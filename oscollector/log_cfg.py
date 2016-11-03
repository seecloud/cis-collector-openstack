import logging
import logging.config
from settings import DEV_LOGGING_CONFIG as LOGGING_CONFIG


def setup_logger():
    """Setup logging configuration
    Logger configured on import
    """

    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        configured_logging = True
        logging.info('Logging configured with application configuration')
    except SyntaxError:
        configured_logging = False
        logging.info('Logging setup from application configuration failed. '
                     'Default configuration will be applied')

    if not configured_logging:
        logging.basicConfig(level=logging.INFO)

setup_logger()
