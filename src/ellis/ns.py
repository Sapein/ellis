"""
This provides the NationStates interface for Ellis.
"""

import time
import threading
import logging
import urllib.request
from xml.etree import ElementTree
from typing import Optional


from ellis import config


VER = "0.0.0"
lock = threading.Lock()


def _set_ver(version):
    global VER  # pylint: disable=W0603
    VER = version


class Limiter:
    """
    This class is a limiter for accessing NationStates, and should
    be locked around.
    """

    requests = 0
    tg_requests = 0
    last_request = None
    last_tg_request = None

    def __init__(self):
        self.last_request = 0
        self.last_tg_request = 0

    def check(self):
        """
        Checks to see when the last normal API request was.

        Notes
        -----
        This will block on call if a request can not be made.
        """
        is_allowed = (self.requests + self.tg_requests) < 50
        is_allowed = is_allowed or self.last_request + 62 < time.time()
        if is_allowed:
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
        """
        Checks to see when the last TG API request was.

        See Also
        --------
        check : Checks when the last regular API Request.

        Notes
        -----
        This uses the stricter recruitment restrictions, due to this
        largely being meant for autotelegramming.
        This will eventually be removed in future.
        """

        nontg_request = self.requests + self.tg_requests
        nontg_request = nontg_request and self.last_request + 60 < time.time()
        tg_request = self.tg_requests <= 1
        tg_request = tg_request and (self.last_tg_request + 180) < time.time()
        if nontg_request and tg_request:
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
    """
    An object repesenting state and all necessary information needed
    for calling the NationStates API.

    Parameters
    ----------
    limiter : Limiter
        The NationStates API Limiter.
    logger : logging.Logger
        A logging object, By default it is the "NS" Logger.

    Attributes
    ----------
    ns_nation_url : str
        A string representation of the first
        part of the NationStates URL for nation shards.
    ns_world_url : str
        A string representatino of the first part of the
        NationStates URL for the world.
    """
    ns_nation_url = "https://www.nationstates.net/cgi-bin/api.cgi?nation="
    ns_world_url = "https://www.nationstates.net/cgi-bin/api.cgi?q="

    def __init__(self, limiter, logger=logging.getLogger("NS")):
        self.limiter = limiter
        self.log = logger

        nation = config.Config['Core']['NS_Nation']
        region = config.Config['Core']['NS_Region']

        nation_conf = nation.lower() == "unknown"
        nation_conf = nation or bool(nation)
        region_conf = region.lower() == "unknown"
        region_conf = region or bool(region)

        if nation_conf:
            raise ValueError("You MUST provide a Nation!")
        if region_conf:
            raise ValueError("You MUST provide a Region!")

    def _send_request(self, url):
        """ Actually sends the request and returns the raw stuff. """
        self.limiter.check()
        url = url.replace(" ", "_")
        user_agent = ("Ellis v{} - written by Dusandria Founder (Chanku#4372),"
                      "request for {} on behalf of {}"
                      ).format(VER,
                               config.Config['Core']['NS_Nation'],
                               config.Config['Core']['NS_Region'])
        request = urllib.request.Request(url,
                                         headers={'User-Agent': user_agent})
        with urllib.request.urlopen(request) as request:
            return request.read().decode('utf-8')

    def get_nation_xml(self, nation_name: str) -> str:
        """ Sends a Request to get the raw XML of a nation """
        return self._send_request('{}{nation}'.format(self.ns_nation_url,
                                                      nation=nation_name))

    def get_nation(self, nation_name: str) -> dict[str, str]:
        """ Returns a Dictionary-Like Object of a nation. """
        nation_name = nation_name.replace(" ", "_")
        nation_xml = self.get_nation_xml(nation_name)
        nation_root = ElementTree.fromstring(nation_xml)
        parsed_nation = self._parse_element(nation_root)
        try:
            return parsed_nation['nation']
        except KeyError:
            return parsed_nation

    def _parse_element(self, tree):
        if len(tree) == 0:  # pylint: disable=no-else-return
            return {tree.tag.lower(): tree.text}
        else:
            new_dict = {}
            for child in tree:
                new_dict.update(self._parse_element(child))
            return {tree.tag.lower(): new_dict}

    def get_nation_recruitable(self, nation: str,
                               region: Optional[str] = None) -> bool:
        """ Sends a Request and returns True if it is able to be sent
        a recruitment TG, and False if it is not. A region is optional,
        and will add that into the query"""
        nation = nation.replace(" ", "_")
        query = '&q=tgcanrecruit'
        if region is not None:
            query = "{};region={region}".format(nation, region=region)
        response = self._send_request(('{}{nation}{query}'
                                       ).format(self.ns_nation_url,
                                                nation=nation,
                                                query=query))
        response = self._parse_element(ElementTree.fromstring(response))
        can_recruit = response['nation']['tgcanrecruit']
        if can_recruit == "1":  # pylint: disable=no-else-return
            return True
        elif can_recruit == "0":
            return False
        else:
            raise SyntaxError("UNKNOWN RESPONSE: {}".format(response))

    def get_foundings(self):
        """ Requests a list of recent foundings from NationStates, and
        then returns a Dictionary of Recent Foundings. """
        foundings_xml = self._send_request(('{}happenings;filter=founding'
                                            ).format(self.ns_world_url))
        hapenings_root = ElementTree.fromstring(foundings_xml)[0]
        foundings = []
        for founding in hapenings_root:
            timestamp = founding[0].text
            nation = founding[1].text.split("@@")[1]
            region = founding[1].text.split("%%")[1]
            foundings.append({'name': nation,
                              'founding_region': region,
                              'founded_at': timestamp})
        return foundings


class NS_Telegram():  # pylint: disable=C0103,R0903
    """
    An object repesenting state and all necessary information needed
    for calling the NationStates API.

    Parameters
    ----------
    limiter : Limiter
        The NationStates API Limiter.
    tgid : str
        The Telegram ID for the Telegram you wish to send.
    tg_key : str
        The Telegram Key for the Telegram you wish to send.
    api_key : str
        The Unique API Key to send a telegram.

    Attributes
    ----------
    ns_tg_url : str
        A String representation of the base URL to send Telegram
        Requests to.

    See Also
    --------
    NS : The NationStates Request Object
    """

    ns_tg_url = ('https://www.nationstates.net/cgi-bin/'
                 'api.cgi?a=sendTG&client={client}&tgid={tgid}&key={key}&to='
                 )

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
        url = url.replace(' ', "_")
        user_agent = ("Ellis v{} - written by Dusandria Founder (Chanku#4372),"
                      "request for {} on behalf of {}"
                      ).format(VER,
                               config.Config['Core']['NS_Nation'],
                               config.Config['Core']['NS_Region'])
        request = urllib.request.Request(url,
                                         headers={'User-Agent': user_agent})
        with urllib.request.urlopen(request) as request:
            return request.read().decode('utf-8')


limit = Limiter()
