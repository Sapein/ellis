""" This exercises and tests Ellis.py """

import pytest
import socket
import json

TEST_FORMAT = [{'name':'Potato', 'region':'potato'}, {'name':'Potato2', 'region':'potato'}]
TEST_JSON = '[{"name":"Potato","region":"potato"},{"name":"Potato2","region":"potato"}]\n'


@pytest.fixture(autouse=True)
def patch_modules(monkeypatch):
    monkeypatch.delattr('ellis.modules.autorecruit')
    monkeypatch.setattr('ellis.ellis_modules._Ellis_Registry._add_Ellis',
                        classmethod(lambda x, y: 'Potato'))
    monkeypatch.setattr('ellis.ellis_modules._Ellis_Registry.start',
                        classmethod(lambda x: 'Potato'))
    monkeypatch.setattr('ellis.ellis_modules._Ellis_Registry.stop',
                        classmethod(lambda x: 'Potato'))
    yield
    monkeypatch.undo()

@pytest.fixture(autouse=True)
def patch_nation(monkeypatch):
    Core = {'NS_Nation': 'Test',
            "NS_Region": "Test",
            "Hostname": "localhost",
            "Port": 4526}
    monkeypatch.setattr('ellis.config.Config', {'Core':Core})
    yield
    monkeypatch.undo()

from ellis import ellis

@pytest.fixture()
def json_fake_dump_read(monkeypatch):
    def dump(obj, fp, *args, **kwargs):
        print(json.dumps(TEST_FORMAT, sort_keys=True))

    def load(fp, *args, **kwargs):
        return TEST_FORMAT
    monkeypatch.setattr('json.dump', dump)
    monkeypatch.setattr('json.load', load)
    yield
    monkeypatch.undo()

@pytest.fixture(autouse=True)
def hide_actual_files(monkeypatch, tmp_path):
    rented = tmp_path / "rented_nations"
    available = tmp_path / "available_nations"
    recruited = tmp_path / "recruited_nations"
    monkeypatch.setattr('ellis.ellis.AVAILABLE_JSON_PATH', available.as_posix())
    monkeypatch.setattr('ellis.ellis.RENTED_JSON_PATH', rented.as_posix())
    monkeypatch.setattr('ellis.ellis.RECRUITED_JSON_PATH', recruited.as_posix())
    yield
    monkeypatch.undo()

def test_read_in(json_fake_dump_read, tmp_path):
    d = tmp_path / "somefile"
    d.write_text('dork')
    new_ellis = ellis.EllisServer()
    assert new_ellis._read_in(d.as_posix()) == TEST_FORMAT

def test_write_out(capsys, json_fake_dump_read):
    ellis.EllisServer()._write_out(location=ellis.RENTED_JSON_PATH, state_list=TEST_FORMAT)
    captured = capsys.readouterr()
    assert captured.out.replace(" ", "") == TEST_JSON

def test_instantiation():
    new_ellis = ellis.EllisServer()
    assert new_ellis

def test_start():
    new_ellis = ellis.EllisServer()
    new_ellis.start()
    assert new_ellis.running

def test_stop():
    new_ellis = ellis.EllisServer()
    new_ellis.start()
    new_ellis.stop()
    assert not new_ellis.running

@pytest.mark.parametrize('nation, blacklist, expected',
                         [
                             ({'name':'Potato'},
                              {'name':{'exact':['potato'], 'partial':[]}}, True),
                             ({'name':'Potato'},
                              {'name':{'partial':['to'], 'exact':[]}}, True),
                             ({'name':'Potato'},
                              {'name':{'partial':['tata'], 'exact':['tato']}}, False)
                         ])
def test_filter_nation(nation, blacklist, expected):
    new_ellis = ellis.EllisServer()
    new_ellis.blacklists = blacklist
    assert new_ellis.filter_nation(nation) == expected

def test_filter_nation_bad():
    new_ellis = ellis.EllisServer()
    new_ellis.blacklists = {'err':{'exact':[], 'partial':[]}}
    assert new_ellis.filter_nation({'name':'potato'}) == False

def test_filter_nations():
    blacklist = {'name':{'exact':["Potato"], 'partial':['tata']}}
    nations = [{'name':'Potato'}, {'name':"potata"}, {"name":"Taco Supreme"}]
    new_ellis = ellis.EllisServer()
    new_ellis.blacklists = blacklist
    assert new_ellis.filter_nations(nations) == [{"name":"Taco Supreme"}]

@pytest.fixture()
def monkeypatch_sockets(monkeypatch):
    def recv(self, b, c=['GET', 'END', 'GET']): 
        return c.pop().encode('utf-8')
    def send(self, b):
        print(b.decode('utf-8'))
    def shutdown(self, b):
        return b
    def close(self):
        return self
    monkeypatch.setattr('socket.socket.recv', recv)
    monkeypatch.setattr('socket.socket.send', send)
    monkeypatch.setattr('socket.socket.close', close)
    monkeypatch.setattr('socket.socket.shutdown', shutdown)
    yield
    monkeypatch.undo()

@pytest.fixture()
def monkeypatch_ns(monkeypatch):
    monkeypatch.setattr('ellis.ns.NS.get_nation', lambda y, x: {'name':x})
    monkeypatch.setattr('ellis.ns.NS.get_nation_recruitable', lambda y, x: True)
    yield
    monkeypatch.undo()

@pytest.mark.skip() # This test isn't working right for right now. So we skip it.
def test_handle_client(capsys, monkeypatch_sockets, monkeypatch_ns):
    s = socket.socket()
    new_ellis = ellis.EllisServer()
    new_ellis.available_nations = [{'name':'Potato'}, {'name':'Potato'}]
    new_ellis.start()
    new_ellis.handle_client(s, ('', 1))
    new_ellis.stop()
    captured = capsys.readouterr()
    print(captured)
    assert False

def test_setver():
    ellis._set_ver()
    from ellis import ns
    assert ns.VER == ellis.__version__
