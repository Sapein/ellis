"""
This module is mostly a shell to start up Ellis
and organize what is necessary. This may be modified.
"""

import logging

from ellis import ellis, config

LOG_FORMAT = '%(asctime)s - %(threadName)s :: %(message)s'

if __name__ == "__main__":
    handler = logging.StreamHandler()
    file_handler = logging.FileHandler("./output")
    handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    config.read_in()
    ellis._set_ver()
    server = ellis.EllisServer(hostname=config.Config['Core']['Hostname'],
                               port=int(config.Config['Core']['Port']))
    server.log.setLevel(logging.DEBUG)
    server.log.addHandler(handler)
    server.log.addHandler(file_handler)
    server.start()
    server.run()
