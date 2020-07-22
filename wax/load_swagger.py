from typing import Dict, Any
import json
import jsonschema
import itertools
import datetime
from pathlib import Path
from wax.load_config import config
from wax.pack_util import packed, dir_mtime
from wax.jsonschema_util import jsonschema_to_rows


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
            print('Reloaded at %s.' % datetime.datetime.fromtimestamp(int(last_modify)))
        return cls.swagger_data


def parse_operation(swagger_data, endpoint:Dict, method:str) -> Dict:
    """
    :return {'params': ..., 'requests': ..., 'responses': ...}
    """
    operation = endpoint[method.lower()]
    data = {'params': {}, 'requests': [], 'responses': []}
    params = {'path': [], 'query': [], 'header': []}
    for param in itertools.chain(endpoint.get('parameters', []), operation.get('parameters', [])):
        for source in params.keys():
            if param['in'] == source:
                params[source].append(param)
    data['params'].update(params)
    for status_code, response_val in operation.get('responses', {}).items():
        for content_key, content_val in response_val['content'].items():
            data['responses'].append({
                'status_code': status_code,
                'content_type': content_key,
                'rows': jsonschema_to_rows('', '+', content_val.get('schema', {}), swagger_data, required=[]),
                'examples': {key: json.dumps(val['value'], ensure_ascii=False, indent=4)
                             for key, val in content_val.get('examples', {}).items()}
            })
    for content_key, content_val in operation.get('requestBody', {}).get('content', {}).items():
        data['requests'].append({
            'content_type': content_key,
            'rows': jsonschema_to_rows('', '+', content_val.get('schema', {}), swagger_data, required=[])
        })
    return data
