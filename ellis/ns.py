import time
import threading
import urllib.request
import xml.etree.ElementTree as ElementTree

from typing import Optional



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


class L():
    def info(*args, **kwargs):
        pass

    def debug(*args, **kwargs):
        pass

lock = threading.Lock()
class Limiter:
    requests = 0
    tg_requests = 0
    last_request = None
    last_tg_request = None
    def __init__(self):
        self.last_request = 0
        self.last_tg_request = 0

    def check(self):
        if (self.requests + self.tg_requests) < 50 or (self.requests + self.tg_requests >- 50 and self.last_request + 62 < time.time()):
            if (self.requests + self.tg_requests) < 50:
                self.requests += 1
            else:
                self.requests = 0
            self.last_request = time.time()
        else:
            time.sleep(62)
            self.requests = 0
            self.check()

    def check_tg(self):
        normal_request = self.requests + self.tg_requests and (self.last_request + 60) < time.time()
        tg_request = self.tg_requests and (self.last_tg_request + 180) < time.time()
        if normal_request and tg_request:
            if (self.requests + self.tg_requests) < 50:
                self.requests += 1
            else:
                self.requests = 0
            self.last_request = time.time()
        else:
            time.sleep(182)
            self.requests = 0
            self.check()

class NS:
    ns_nation_url = "https://www.nationstates.net/cgi-bin/api.cgi?nation="
    ns_world_url = "https://www.nationstates.net/cgi-bin/api.cgi?q="
    def __init__(self, limiter, logger):
        self.limiter = limiter
        self.logg = logger
        self.log = L() #Let's disable the logger...

    @logcall()
    def _send_request(self, url): 
        """ Actually sends the request and returns the raw stuff. """
        self.log.debug("Checking Limits...")
        self.limiter.check()
        url = url.replace(" ", "_")
        request = urllib.request.Request(url, headers={'User-Agent': 'Ellis.py v 0.1.0 - Dusandria Founder (Chanku#4372)'})
        self.log.debug("Sending Request to URL: {}.".format(url))
        with urllib.request.urlopen(request) as request:
            self.log.debug("Request Decoding!")
            return request.read().decode('utf-8')

    @logcall()
    def get_nation_XML(self, nation):
        """ Sends a Request to get the raw XML of a nation """
        return self._send_request('{}{nation}'.format(self.ns_nation_url, nation=nation))

    @logcall()
    def get_nation(self, nation):
        """ Returns a Dictionary-Like Object of a nation. """
        nation = nation.replace(" ", "_")
        nation_xml = self.get_nation_XML(nation)
        nation_root = ElementTree.fromstring(nation_xml)
        a = self._parse_element(nation_root)
        try:
            return a['nation']
        except KeyError:
            return a

    def _parse_element(self, tree):
        if len(tree) == 0:
            return {tree.tag.lower(): tree.text}
        else:
            new_dict = {}
            for child in tree:
                new_dict.update(self._parse_element(child))
            return {tree.tag.lower(): new_dict}

    @logcall()
    def get_nation_recruitable(self, nation:str, region: Optional[str]=None) -> bool:
        """ Sends a Request and returns True if it is able to be sent a recruitment TG,
        and False if it is not. A region is optional, and will add that into the query"""
        nation = nation.replace(" ", "_")
        query = '&q=tgcanrecruit'
        if not region is None:
            query = "{};region={region}".format(nation, region=region)
        response = self._send_request('{}{nation}{query}'.format(self.ns_nation_url,
                                                                 nation=nation,
                                                                 query=query))
        response = self._parse_element(ElementTree.fromstring(response))
        if response['nation']['tgcanrecruit'] == "1":
            return True
        elif response['nation']['tgcanrecruit'] == "0":
            return False
        else:
            raise SyntaxError("UNKNOWN RESPONSE: {}".format(response))

    @logcall()
    def get_foundings(self):
        """ Requests a list of recent foundings from NationStates, and
        then returns a Dictionary of Recent Foundings. """
        self.log.debug("Sending NS Request")
        foundings_xml = self._send_request('{}happenings;filter=founding'.format(self.ns_world_url))
        self.log.debug("XML: {}".format(foundings_xml))
        self.log.debug("Got the Root!")
        hapenings_root = ElementTree.fromstring(foundings_xml)[0]
        foundings = []
        for founding in hapenings_root:
            timestamp = founding[0].text
            nation = founding[1].text.split("@@")[1] 
            region = founding[1].text.split("%%")[1]
            foundings.append({'name':nation, 'founding_region':region, 'founded_at':timestamp})
            self.log.debug("Response: {}".format(foundings[-1]))
        return foundings

class NS_Telegram():
    ns_tg_url = 'https://www.nationstates.net/cgi-bin/api.cgi?a=sendTG&client={client}&tgid={tgid}&key={key}&to='
    def __init__(self, limiter, tgid, tg_key, api_key):
        self.ns_tg_url = self.ns_tg_url.format(client=api_key,
                                               tgid=tgid,
                                               key=tg_key)
        self.limiter = limiter
    def send_telegram(self, recipient):
        """ Send a Recruitment Telegram to Recipient. """
        self.limiter.check_tg()
        recipient = recipient.replace(" ", "_")
        self._send_request('{}{}'.format(self.ns_tg_url, recipient))
        
    def _send_request(self, url): 
        """ Actually sends the request and returns the raw stuff. """
        self.limiter.check()
        request = urllib.request.Request(url, headers={'User-Agent': 'Ellis.py v 0.1.0 - Recruitment Attachment - Dusandria Founder (Chanku#4372)'})
        with urllib.request.urlopen(request) as request:
            return request.read().decode('utf-8')

limit = Limiter()
