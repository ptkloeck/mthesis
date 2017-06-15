'''
Created on Apr 3, 2016

@author: peter
'''
import json
import os.path
import sys


# CONFIG_FILE = "config_frink.json"
CONFIG_FILE = "config.json"

ws_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
print(ws_path)
config_path = os.path.join(ws_path, "config/" + CONFIG_FILE)
with open(config_path) as config_file:
    config = json.load(config_file)

def path_to_res(res_id):
    return os.path.join(ws_path, config[res_id])

def is_linux():
    platform = sys.platform
    return platform == "linux" or platform == "linux2"
