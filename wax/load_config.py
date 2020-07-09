import json

try:
    config = json.loads(open('config.json').read())
except:
    config = {}
