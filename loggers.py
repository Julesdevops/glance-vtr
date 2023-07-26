import logging

def initialize():
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    logger.addHandler(console)
