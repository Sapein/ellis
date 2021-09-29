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


def add_module_config(module, configs):
    global Config
    Config[module] = configs

def remove_module_config(module):
    global Config
    del Config[module]

def read_in():
    global Config
    try:
        with open(config_path, 'r') as f:
            Config = json.loads(f.read())
    except:
        pass

def write_out():
    print("Printing")
    with open(config_path, 'w') as f:
        print("WRITING")
        f.write(json.dumps(Config, sort_keys=True, indent=4))
        print("WROTE")
