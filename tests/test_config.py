""" Tests the configuration system. """
import pytest
import json

from ellis import config

DEFAULT_CONFIG = {
    'Core': {
        'Hostname': 'localhos',
        'Port': '4526',
        'NS_Region': "Unknown",
        'NS_Nation': "Unknown",
    },
}  # pylint: disable=C0103

@pytest.fixture()
def json_fake_read_bad(monkeypatch):
    def load(fp, *args, **kwargs):
        raise FileNotFoundError
    monkeypatch.setattr('json.load', load)
    yield
    monkeypatch.undo()

def test_default():
    assert config.Config == {'Core': {
        'Hostname':'localhost',
        'Port':'4526', 'NS_Region':"Unknown",
        "NS_Nation":"Unknown"}}

def test_add_config():
    config.add_module_config("Test", {"Test_Val":1})
    assert "Test" in config.Config
    assert config.Config["Test"] == {"Test_Val":1}

def test_remove_config(monkeypatch):
    assert "Test" in config.Config
    config.remove_module_config("Test")
    assert "Test" not in config.Config

@pytest.fixture()
def json_fake_dump_read(monkeypatch):
    def dump(obj, fp, *args, **kwargs):
        print(json.dumps(DEFAULT_CONFIG, sort_keys=True))

    def load(fp, *args, **kwargs):
        return DEFAULT_CONFIG
    monkeypatch.setattr('json.dump', dump)
    monkeypatch.setattr('json.load', load)
    yield
    monkeypatch.undo()

def test_write_out(monkeypatch, capsys, json_fake_dump_read):
    config.write_out()
    captured = capsys.readouterr()
    assert captured.out.replace(' ','').strip() == ('{"Core":{"Hostname":"localhos",'
                               '"NS_Nation":"Unknown",'
                               '"NS_Region":"Unknown","Port":"4526"}}')

def test_read_in_bad(monkeypatch, capsys, json_fake_read_bad):
    config.read_in()
    assert config.Config != DEFAULT_CONFIG

def test_read_in(monkeypatch, capsys, json_fake_dump_read):
    config.read_in()
    assert config.Config == DEFAULT_CONFIG

