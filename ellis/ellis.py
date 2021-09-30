import json
import socket
import threading
import time
import urllib.error

import logging

import config
import ellis_modules
import ns

__version__ = "1.0.0"

def logcall(message_prefix="Calling: {}"):
    def _logcall(fn):
        def f(*args, **kwargs):
            msg = message_prefix.format(fn.__qualname__)
            args[0].log.debug(msg)
            result = fn(*args, **kwargs)
            args[0].log.debug("{}: DONE!".format(fn.__qualname__))
            return result
        return f
    return _logcall

class EllisServer:
    blacklists: dict = {}
    available_nations: list[dict] = []
    rented_nations: list[dict] = []
    recruited_nations: list[dict] = []
    log = logging.getLogger("Ellis")

    recruitment_thread = None
    def __init__(self, hostname:str ='localhost', port:int=4526):
        self.queue: list= []
        self.Threads: list[threading.Thread] = []
        self.hostname = hostname
        self.port = port
        self.running: bool = False
        self.ns = ns.NS(ns.limit, self.log)
        ellis_modules._Ellis_Registry._add_Ellis(self)

    @logcall()
    def start(self):
        self.available_nations = self._read_in('./saved_nations')
        self.recruited_nations = self._read_in('./recruited_nations')
        self.rented_nations = self._read_in('./rented_nations')
        self.blacklists['names'] = self._read_in('./name_blacklist')
        config.read_in()
        self.running = True
        ellis_modules._Ellis_Registry.start()

    @logcall()
    def pull_nations(self):
        """ Pulls Nations from NationStates to autopopulate the Queue. """
        while self.running:
            self.log.debug("Sending Request to NS")
            new_nations = self._get_recruitable()
            self.available_nations.extend(new_nations)
        self.available_nations = list(set(self.available_nations))

    @logcall()
    def run(self):
        try:
            self.log.info("Establishing Server...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.hostname, self.port))
            self.log.debug("Listening...")
            s.listen(5)
            self.log.info("Starting Pulling...")
            self.Threads.append(threading.Thread(target=self.pull_nations))
            self.Threads[-1].start()
            self.log.info("Starting Client Modules...")

            self.log.debug("Entering Main Loop...")
            while self.running:
                self.log.info("Waiting for Client...")
                client, address = s.accept()
                self.log.debug("Client accepted!")
                self.Threads.append(threading.Thread(target=self.handle_client, args=[client, address]))
                self.log.debug("Client Running!")
                self.Threads[-1].start()
                time.sleep(10)

            self.log.info("Goodbye!!!")
        finally:
            self.stop()
            try:
                s.shutdown(SHUT_RDWR)
                s.close()
                for thread in self.Threads:
                    thread.join()
            except:
                pass

    def _check_nation(self, nation_name: str) -> bool:
        """ Checks to see if a nation is recruitable. """
        with ns.lock:
            return self.ns.get_nation_recruitable(nation_name)

    @logcall()
    def _get_recruitable(self) -> list[dict]:
        """ Gets the most recently recruitable nations. """
        with ns.lock:
            _foundings = self.ns.get_foundings()
        foundings = []
        for founding in _foundings:
            try:
                with ns.lock:
                    nation_info = self.ns.get_nation(founding['name'])
                    founding.update(nation_info)
                foundings.append(founding)
            except urllib.error.HTTPError as e:
                self.log.error(e)
                if e.code == 404:
                    pass
                else:
                    raise

        return foundings

    @logcall()
    def _checkout_nation(self) -> dict:
        with ns.lock:
            try:
                nation = self.available_nations.pop()
            except IndexError:
                return None
            self.rented_nations.append(nation)

        return nation

    def _return_nation(self, nation: dict):
        self.log.info("Returning Nation: {}".format(nation))
        if not self._check_nation(nation['name']):
            with ns.lock:
                self.rented_nations.remove(nation)
                self.recruited_nations.append(nation)
        else:
            with ns.lock:
                self.rented_nations.remove(nation)
                self.available_nations.append(nation)

    def handle_client(self, client, address):
        self.log.info("Handling Client: {}".format(str(address)))
        client_closed = False
        try:
            while self.running:
                self.log.debug("Waiting for Command...")
                command = client.recv(2048).decode('utf-8')
                self.log.debug("Command Reciveved From: {}. Command: {}".format(str(address), command))
                if command.lower().split(' ')[0] == 'return' and command.lower().split('return ')[1]:
                    self.log.info("Returning Nation!")
                    self._return_nation(json.loads(command[len('return '):]))
                elif command.lower().split(' ')[0] == 'check':
                    self.log.info("Checking Nation!")
                    if self._check_nation(command.lower().split('check ')[1]):
                        client.send(json.dumps({'recruitable': 1}).encode('utf-8'))
                    else:
                        client.send(json.dumps({'recruitable': 0}).encode('utf-8'))
                elif command.lower().split(' ')[0] == 'end':
                    client_closed = True
                    break
                elif command.lower() == 'get':
                    self.log.info("Sending Nation!")
                    while True:
                        nation = self._checkout_nation()
                        if nation and self._check_nation(nation['name']):
                            client.send(json.dumps(nation).encode('utf-8'))
                            break
                        else:
                            self.log.debug("Waiting until a nation is available...")
                            self.log.debug("Nation: {}".format(nation))
                            time.sleep(30)
        except BaseException as e:
            self.log.error(e, exc_info=1)
            raise
        finally:
            if not client_closed:
                client.send("END".encode('utf-8'))
            self.log.info("Disconnecting!")
            client.shutdown(socket.SHUT_RDWR)
            client.close()

    def stop(self):
        self.running = False
        ellis_modules._Ellis_Registry.stop()
        self._write_out(self.available_nations, './saved_nations')
        self._write_out(self.rented_nations, './rented_nations')
        self._write_out(self.recruited_nations, './recruited_nations')
        config.write_out()

    @logcall()
    def _read_in(self, location: str) -> list[dict]:
        self.log.info("Reading in: {}".format(location))
        nations = []
        try:
            with open(location, 'r') as f:
                nations = json.loads(f.read())
        except:
            pass

        return nations

    @logcall()
    def _write_out(self, state_list: list[dict], location: str):
        self.log.info("Writing Out to: {}".format(location))
        try:
            with open(location, 'w') as f:
                f.write('[')
                for s in state_list:
                    f.write(json.dumps(s))
                    f.write(',\n')
                f.write(']')
        except:
            pass

ns.set_ver(__version__)
