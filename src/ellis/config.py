"""
This is just a simple module for configuring stuff.
"""

import json

# pylint: disable=W0603,W0602


CONFIG_PATH = "./ellis.conf"

Config = {
    'Core': {
        'Hostname': 'localhost',
        'Port': '4526',
        'NS_Region': "Unknown",
        'NS_Nation': "Unknown",
    },
}  # pylint: disable=C0103


def add_module_config(module_name: str, configs: dict[str, str]):
    """
    Adds in a config for a module,

    Parameters
    ----------
    module_name : str

    configs : dict
        The 'default' configuration provided by the module.
    """
    Config[module_name] = configs


def remove_module_config(module_name: str):
    """
    Removes the configuration from the global config.

    Parameters
    ----------
    module_name : str

    Raises
    ------
    KeyError
        When the module has not been added/already removed from the config.
    """
    global Config
    del Config[module_name]


def read_in():
    """
    Reads in the Configruation File.
    """
    global Config
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            Config = json.load(file)
    except (OSError, IOError):
        pass


def write_out():
    """
    Writes out the Configuration File
    """
    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
        json.dump(Config, file, sort_keys=True, indent=4)
