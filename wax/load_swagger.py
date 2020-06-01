from typing import Dict, Any
import json
import jsonschema
from os.path import getmtime


class SwaggerData:
    json_path = ''
    redis_prefix = 'waxapi::'
    swagger_data: Dict = {}
    resolver = None
    last_modify = 0

    @classmethod
    def init(cls, json_path):
        cls.json_path = json_path
        cls.last_modify = getmtime(json_path)
        cls.swagger_data = json.loads(open(json_path).read())
        cls.resolver = jsonschema.RefResolver.from_schema(cls.swagger_data)
        cls.redis_prefix = 'waxapi::' + cls.swagger_data['info']['title'] + '::' + cls.swagger_data['info']['version'] + '::'

    @classmethod
    def get(cls) -> Dict:
        last_modify = getmtime(cls.json_path)
        if last_modify != cls.last_modify:
            cls.swagger_data = json.loads(open(cls.json_path).read())
            cls.resolver = jsonschema.RefResolver.from_schema(cls.swagger_data)
            cls.last_modify = last_modify
        return cls.swagger_data
