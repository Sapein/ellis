"""
This module is mostly a shell to start up Ellis
and organize what is necessary. This may be modified.
"""

import logging

from ellis import ellis

LOG_FORMAT = '%(asctime)s - %(threadName)s :: %(message)s'

if __name__ == "__main__":
    server = ellis.EllisServer()
    server.log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    file_handler = logging.FileHandler("./output")
    handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    server.log.addHandler(handler)
    server.log.addHandler(file_handler)
    server.start()
    server.run()
