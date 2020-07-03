from typing import Dict, Any
import json
import jsonschema
from os.path import getmtime
from pathlib import Path
from wax.load_config import config
from wax.pack_util import packed, dir_mtime


class SwaggerData:
    json_path = ''
    redis_prefix = 'waxapi::'
    swagger_data: Dict = {}
    resolver = None
    last_modify = 0

    @classmethod
    def init(cls, json_path):
        title, version = config['title'], config['version']
        if not title:
            print('Title cannot be empty, please edit config.json!')
            exit(1)
        if not version:
            print('Version cannot be empty, please edit config.json!')
            exit(1)
        if not Path(json_path).is_dir():
            print(f'{json_path} is not exist or is not directory!')
        cls.json_path = json_path
        cls.last_modify = dir_mtime(json_path)
        cls.swagger_data = packed(json_path, title, version)
        cls.resolver = jsonschema.RefResolver.from_schema(cls.swagger_data)
        cls.redis_prefix = 'waxapi::' + title + '::' + version + '::'

    @classmethod
    def get(cls) -> Dict:
        last_modify = dir_mtime(cls.json_path)
        if last_modify != cls.last_modify:
            title, version = config['title'], config['version']
            cls.swagger_data = packed(cls.json_path, title, version)
            cls.resolver = jsonschema.RefResolver.from_schema(cls.swagger_data)
            cls.last_modify = last_modify
        return cls.swagger_data
