from pathlib import Path
import json
import os
from wax.load_swagger import SwaggerData


def unpack(json_path):
    """
    json_path_file -> parts/(api.json|paths|components)
    """
    SwaggerData.init(json_path=json_path)
    Path('parts').mkdir(parents=True, exist_ok=True)
    Path('parts/paths').mkdir(parents=True, exist_ok=True)
    Path('parts/components').mkdir(parents=True, exist_ok=True)
    swagger_data = SwaggerData.get()
    for filename in sorted(os.listdir('parts/paths')):
        os.remove(f'parts/paths/{filename}')
    if 'paths' in swagger_data:
        for path_key, path_val in swagger_data['paths'].items():
            filename = path_key.replace('/', '_')
            content = json.dumps({'key': path_key, 'value': path_val}, ensure_ascii=False, indent=2)
            with Path(f'parts/paths/{filename}.json').open('w', encoding='utf-8') as f:
                f.write(content)

    for filename in sorted(os.listdir('parts/components')):
        os.remove(f'parts/components/{filename}')
    if 'components' in swagger_data and 'schemas' in swagger_data['components']:
        for comp_key, comp_val in swagger_data['components']['schemas'].items():
            content = json.dumps({'key': comp_key, 'value': comp_val}, ensure_ascii=False, indent=2)
            with Path(f'parts/components/{comp_key}.json').open('w', encoding='utf-8') as f:
                f.write(content)

    swagger_data['paths'] = {}
    swagger_data['components'] = {}
    content = json.dumps(swagger_data, ensure_ascii=False, indent=2)
    with Path(f'parts/api.json').open('w', encoding='utf-8') as f:
        f.write(content)


def pack(json_path):
    """
    parts/* -> json_path_file
    """
    swagger_data = json.load(open('parts/api.json'))
    swagger_data.setdefault('paths', {})
    swagger_data.setdefault('components', {})
    swagger_data['components'].setdefault('schemas', {})
    for filename in sorted(os.listdir('parts/paths')):
        if filename.endswith('.json'):
            content = json.load(open(f'parts/paths/{filename}'))
            key, value = content['key'], content['value']
            swagger_data['paths'][key] = value

    for filename in sorted(os.listdir('parts/components')):
        if filename.endswith('.json'):
            content = json.load(open(f'parts/components/{filename}'))
            key, value = content['key'], content['value']
            swagger_data['components']['schemas'][key] = value

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_path)
