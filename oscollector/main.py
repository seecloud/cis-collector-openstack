def main():
    """ Main runner

    Configure logger and run collector instance forever
    """
    import log_cfg
    import logging
    from oscollector import OSCollector
    logger = logging.getLogger(__name__)
    logger.info('Create collector')
    osc = OSCollector()

    while 1:
        osc.collect()


if __name__ == '__main__':
    main()
