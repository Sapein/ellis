""" This file tests the minimal NS API. """

from xml.etree import ElementTree
from time import time
from ellis import ns

import pytest


class test_globals():
    """ Tests the global stuff."""
    assert ns.VER == "0.0.0"
    ns._set_ver("1.0.0")
    assert ns.VER == "1.0.0"
    assert isinstance(ns.limit, ns.Limiter)


class TestLimiter:
    """ Tests the NS.py Limiter Logic. """
    def test_creation(self):
        limit = ns.Limiter()
        assert limit.requests == 0
        assert limit.last_request == 0
        assert limit.tg_requests == 0

    def test_check(self):
        limit = ns.Limiter()
        limit.check()
        assert limit.requests >= 1
        assert limit.tg_requests == 0
        assert bool(limit.last_request)

    def test_after50(self):
        limit = ns.Limiter()
        limit.requests = 50
        limit.check()
        assert limit.requests < 50
        assert limit.requests == 1

    def test_after50tg(self):
        limit = ns.Limiter()
        limit.requests = 49
        limit.tg_requests = 1
        limit.check()
        assert limit.requests == 1

    def test_toosoon(self):
        limit = ns.Limiter()
        limit.last_request = time() - 50
        limit.check()
        assert limit.requests == 1

    def test_toosoon_after50(self, monkeypatch):
        def rewrite(x, y):
            y.last_request = 0
            return x
        limit = ns.Limiter()
        monkeypatch.setattr("time.sleep",
                            lambda x: rewrite(x, limit))
        limit.last_request = time() - 30
        limit.requests = 50
        limit.check()
        assert limit.requests == 1

    def test_toosoon_after50tg(self, monkeypatch):
        def rewrite(x, y):
            y.last_request = 0
            return x
        limit = ns.Limiter()
        monkeypatch.setattr("time.sleep",
                            lambda x: rewrite(x, limit))
        limit.last_request = time() - 30
        limit.requests = 49
        limit.tg_requests = 1
        limit.check()
        assert limit.requests == 1

    def test_check_tg(self):
        limit = ns.Limiter()
        limit.check_tg()
        assert limit.tg_requests == 1
        assert limit.requests == 0
        assert bool(limit.last_tg_request)

    def test_after50_tg(self):
        limit = ns.Limiter()
        limit.requests = 50
        limit.check_tg()
        assert limit.tg_requests == 1
        assert limit.requests == 50

    def test_after50tg_tg(self):
        limit = ns.Limiter()
        limit.requests = 49
        limit.tg_requests = 1
        limit.check_tg()
        assert limit.requests == 49
        assert limit.tg_requests == 2

    def test_toosoon_tg(self, monkeypatch):
        limit = ns.Limiter()
        def rewrite(x):
            limit.last_tg_request = 0
            limit.tg_requests = 0
            limit.requests = 0
            return x
        monkeypatch.setattr("time.sleep",
                            lambda x: rewrite(x))
        limit.last_tg_request = time() + 180
        limit.check_tg()
        assert limit.tg_requests == 1

    def test_toosoon_after50_tg(self, monkeypatch):
        limit = ns.Limiter()
        def rewrite(x):
            limit.last_tg_request = 0
            limit.tg_requests = 0
            limit.requests = 0
            return x
        monkeypatch.setattr("time.sleep",
                            lambda x: rewrite(x))
        limit.last_request = time() + 180
        limit.requests = 50
        limit.check_tg()
        assert limit.tg_requests == 1

    def test_toosoon_after50tg_tg(self, monkeypatch):
        limit = ns.Limiter()
        def rewrite(x):
            limit.last_tg_request = 0
            limit.tg_requests = 0
            limit.requests = 0
            return x
        monkeypatch.setattr("time.sleep",
                            lambda x: rewrite(x))
        limit.last_tg_request = time() + 180
        limit.tg_requests = 1
        limit.check_tg()
        assert limit.tg_requests == 1



class MockRequest:
    rval = None
    def __init__(self, rval):
        self.rval = rval

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def read(self):
        return self.rval

REQUEST_XML = "<NATION>test</NATION>"

SIMPLE_XML = "<NATION>test</NATION>"
SIMPLE_PARSED = {'nation':'test'}
NESTED_XML = "<NATION><NAME>test</NAME></NATION>"
NESTED_PARSED = {'nation':{'name':'test'}}
COMPLEX_XML = "<ROOT><NATION>test</NATION><REGION><NAME>test</NAME></REGION></ROOT>"
COMPLEX_PARSED = {'root':{'nation':'test', 'region':{'name':'test'}}}
FOUNDING_XML = ("<WORLD><HAPPENINGS><EVENT>"
                "<TIMESTAMP>0</TIMESTAMP>"
                "<TEXT>@@test@@ in %%test%%</TEXT>"
                "</EVENT></HAPPENINGS></WORLD>")
FOUNDING_PARSED = [{'name':'test',
                    'founding_region':'test',
                    'founded_at':'0'}]

class TestNS:
    """ Tests the ns.py NS Class Logic. """

    @pytest.fixture()
    def mock_request(self, monkeypatch,):
        i = REQUEST_XML.encode('utf-8')
        def patch(*args, **kwargs):
            return MockRequest(i)
        monkeypatch.setattr('urllib.request.urlopen',
                            patch)

    @pytest.fixture(autouse=True)
    def conf(self, monkeypatch):
        conf = {'NS_Nation':'Test',
                'NS_Region':'Test', }
        monkeypatch.setattr('ellis.config.Config',
                            {'Core':conf})

    def test_creation(self):
        nationstates = ns.NS(ns.limit)

    def test_send_request(self, mock_request):
        nationstates = ns.NS(ns.Limiter())
        url = nationstates.ns_nation_url
        data = nationstates._send_request('{}{}'.format(url, "test"))
        assert data == REQUEST_XML

    @pytest.mark.parametrize("test_input,expected",
                             [(SIMPLE_XML, SIMPLE_PARSED),
                              (NESTED_XML, NESTED_PARSED),
                              (COMPLEX_XML, COMPLEX_PARSED)])
    def test_parse_element(self, test_input, expected):
        nationstates = ns.NS(ns.Limiter())
        etree = ElementTree.fromstring(test_input)
        parsed = nationstates._parse_element(etree)
        assert parsed == expected

    def test_foundings(self, monkeypatch):
        monkeypatch.setattr('ellis.ns.NS._send_request',
                            lambda x, y: FOUNDING_XML)
        nationstates = ns.NS(ns.Limiter())
        foundings = nationstates.get_foundings()
        assert foundings == FOUNDING_PARSED

    @pytest.mark.parametrize("test_input, expected",
                             [({'nation':{'tgcanrecruit':'0'}}, False),
                              ({'nation':{'tgcanrecruit':'1'}}, True)])
    def test_get_nation_recruitable(self, mock_request, monkeypatch, test_input, expected):
        monkeypatch.setattr('xml.etree.ElementTree.fromstring',
                            lambda x: test_input)
        monkeypatch.setattr('ellis.ns.NS._parse_element',
                            lambda x, y: y)
        nationstates = ns.NS(ns.Limiter())
        recruitable = nationstates.get_nation_recruitable("test")
        assert recruitable is expected

    @pytest.mark.parametrize("test_input, expected",
                             [({'nation':{'tgcanrecruit':'0'}}, False),
                              ({'nation':{'tgcanrecruit':'1'}}, True)])
    def test_get_nation_recruitable_region(self, mock_request, monkeypatch, test_input, expected):
        monkeypatch.setattr('xml.etree.ElementTree.fromstring',
                            lambda x: test_input)
        monkeypatch.setattr('ellis.ns.NS._parse_element',
                            lambda x, y: y)
        nationstates = ns.NS(ns.Limiter())
        recruitable = nationstates.get_nation_recruitable("test")
        assert recruitable is expected

    def test_get_nation_recruitable_bad(self, mock_request, monkeypatch):
        monkeypatch.setattr('xml.etree.ElementTree.fromstring',
                            lambda x: {'nation':{'tgcanrecruit':'3'}})
        monkeypatch.setattr('ellis.ns.NS._parse_element',
                            lambda x, y: y)
        nationstates = ns.NS(ns.Limiter())
        with pytest.raises(SyntaxError):
            recruitable = nationstates.get_nation_recruitable("test")

    def test_get_nation_XML(self, mock_request):
        assert ns.NS(ns.Limiter()).get_nation_xml("test") == REQUEST_XML

    def test_get_nation(self, mock_request):
        assert ns.NS(ns.Limiter()).get_nation("test") == "test"


class TestNsTg:
    """ Tests the ns.py Telegram Logic. """
    @pytest.fixture()
    def mock_request(self, monkeypatch,):
        i = REQUEST_XML.encode('utf-8')
        def patch(*args, **kwargs):
            return MockRequest(i)
        monkeypatch.setattr('urllib.request.urlopen',
                            patch)

    @pytest.fixture(autouse=True)
    def conf(self, monkeypatch):
        conf = {'NS_Nation':'Test',
                'NS_Region':'Test', }
        monkeypatch.setattr('ellis.config.Config',
                            {'Core':conf})

    def test_creation(self):
        nationstates = ns.NS_Telegram(ns.limit, '', '', '')

    def test_send_request(self, mock_request):
        nationstates = ns.NS_Telegram(ns.Limiter(), '', '', '')
        url = nationstates.ns_tg_url
        data = nationstates._send_request('{}{}'.format(url, "test"))
        assert data == REQUEST_XML

    def test_send_telegram(self, mock_request):
        assert ns.NS_Telegram(ns.Limiter(), '', '', '').send_telegram("test") is None
