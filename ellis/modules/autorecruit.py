"""
This provides autorecruitment functionality into Ellis.
"""

import socket
import time
import json

import config
import ellis_modules
import ns


class Autorecruit(ellis_modules.EllisModule, module_name="Autorecruit"):
    """
    This is the module that providse the core functionality.
    """
    # pylint: disable=abstract-method

    def _auto_tg(self):
        """ This is the actual logic for the recruiter. This is largely
        designed to use the same mechanism as third-party applications so
        that it can be split out easier, especially once I get the auto-loader
        setup. Somes changes might be needed to detach it a bit further, but
        otherwise it is independent. """
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_closed = False
        recruited = []
        nation = None
        try:
            ellis_modules.log.info("Connecting to Ellis...")
            connection.connect(("localhost", 4526))
            ellis_modules.log.info("Connected to Ellis!")
            ellis_modules.log.debug("Entering AutoTG Loop!")
            time.sleep(60)
            while self.running:
                ellis_modules.log.info("Getting Nation...")
                connection.send("GET".encode('utf-8'))
                nation = connection.recv(2048).decode('utf-8')
                if nation.lower() == 'end':
                    server_closed = True
                try:
                    nation = json.loads(nation)
                except json.JSONDecodeError as ex:
                    ellis_modules.log.error(ex, exc_info=1)
                    continue
                ellis_modules.log.info("Recieved Nation!")
                ellis_modules.log.info("Recieved Nation: %s", nation)
                ellis_modules.log.debug("Got Nation: %s", nation['name'])
                ellis_modules.log.debug("Sending Telegram to %s!",
                                        nation['name'])
                with ns.lock:
                    self.ns_tg.send_telegram(nation['name'])
                recruited.append(nation)

            ellis_modules.log.info("Shutting Down!")
        except BaseException as ex:
            ellis_modules.log.error(ex, exc_info=1, stack_info=True)
            raise
        finally:
            ellis_modules.log.info("Returning Nations...")
            for nation in recruited:
                connection.send(('RETURN {}'
                                 ).format(json.dumps(nation)).encode('utf-8'))
            if not server_closed:
                connection.send("END".encode('utf-8'))
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
            ellis_modules.log.info("Goodbye...")
            self.running = False

    def start(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self.running = True
        try:
            self.ns_tg = ns.NS_Telegram(ns.limit,
                                        (config.Config['Autorecruit']
                                         )['NS_TG_ID'],
                                        (config.Config['Autorecruit']
                                         )['NS_Secret_Key'],
                                        (config.Config['Autorecruit']
                                         )['NS_API_Key'])
        except KeyError as ex:
            config.add_module_config(self.module_name,
                                     {
                                         'NS_TG_ID': "Unknown",
                                         'NS_Secret_Key': "Unknown",
                                         'NS_API_Key': "Unknown"
                                     })
            raise SyntaxError("Failed to provide needed ID Keys.") from ex
        while self.running:
            try:
                self._auto_tg()
            except ConnectionRefusedError:
                pass
            except OSError as ex:
                ellis_modules.log.error(ex, exc_info=1)
            except BaseException as ex:
                ellis_modules.log.error(ex, exc_info=1)
                raise

    def stop(self, *args, **kwargs):
        self.running = False
