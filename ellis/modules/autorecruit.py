"""
This is the autorecruit module.
"""
import socket
import time
import logging
import json

import config
import ellis_modules
import ns


class Autorecruit(ellis_modules.Ellis_Module, module_name="Autorecruit"):
    log = logging.getLogger("Ellis")

    def auto_tg(self):
        """ This is the actual logic for the recruiter. This is largely
        designed to use the same mechanism as third-party applications so
        that it can be split out easier, especially once I get the auto-loader
        setup. Somes changes might be needed to detach it a bit further, but
        otherwise it is independent. """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recruited = []
        nation = None
        try:
            self.log.info("Connecting to Ellis...")
            s.connect(("localhost", 4526))
            self.log.info("Connected to Ellis!")
            self.log.debug("Entering AutoTG Loop!")
            time.sleep(60)
            while self.running:
                self.log.info("Getting Nation...")
                s.send("GET".encode('utf-8'))
                nation = s.recv(2048).decode('utf-8')
                try:
                    nation = json.loads(nation)
                except BaseException as e:
                    self.log.error(e, exc_info=1)
                    continue
                self.log.info("Recieved Nation!")
                self.log.info("Recieved Nation: {}".format(nation))
                self.log.debug("Got Nation: {}".format(nation['name']))
                self.log.debug("Sending Telegram to {}!".format(nation['name']))
                with ns.lock:
                    self.ns_tg.send_telegram(nation['name'])
                recruited.append(nation)

            self.log.info("Shutting Down!")
        except BaseException as e:
            self.log.error(e, exc_info=1, stack_info=True)
            raise
        finally:
            self.log.info("Returning Nations...")
            for nation in recruited:
                s.send('RETURN {}'.format(json.dumps(nation)).encode('utf-8'))
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            self.log.info("Goodbye...")
            self.running = False

    def on_load(self, *args, **kwargs):
        self.auto_tg()

    def start(self, *args, **kwargs):
        self.running = True
        try:
            self.ns_tg = ns.NS_Telegram(ns.limit, config.Config['Autorecruit']['NS_TG_ID'], 
                                        config.Config['Autorecruit']['NS_Secret_Key'],
                                        config.Config['Autorecruit']['NS_API_Key'])
        except KeyError:
            config.add_module_config(self.module_name,
                                     {
                                         'NS_TG_ID': "Unknown",
                                         'NS_Secret_Key': "Unknown",
                                         'NS_API_Key': "Unknown"
                                     })
            self.access_Ellis().stop()
            raise SyntaxError("Failed to provide needed ID Keys.")
        while self.running:
            try:
                self.auto_tg()
            except ConnectionRefusedError:
                pass
            except OSError as e:
                self.log.error(e, exc_info=1)
            except BaseException as e:
                self.log.error(e, exc_info=1)
                raise

    def stop(self, *args, **kwargs):
        self.running = False
