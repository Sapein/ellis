"""
This is just a simple module for configuring stuff.
"""

import json

config_path = "./ellis.conf"

Config = {
    'Core': {
        'Hostname': 'localhost',
        'Port': '4526',
        'NS_Region': "Unknown",
        'NS_Nation': "Unknown",
    },
}


def add_module_config(module_name : str, configs : dict[str, str]):
    """
    Adds in a config for a module,

    Parameters
    ----------
    module_name : str

    configs : dict
        The 'default' configuration provided by the module.
    """
    global Config
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
    del Config[module]

def read_in():
    """
    Reads in the Configruation File.
    """
    global Config
    try:
        with open(config_path, 'r') as f:
            Config = json.loads(f.read())
    except:
        pass

def write_out():
    """
    Writes out the Configuration File
    """
    with open(config_path, 'w') as f:
        f.write(json.dumps(Config, sort_keys=True, indent=4))
